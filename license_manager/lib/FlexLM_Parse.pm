#	Copyright 2018 Battelle Energy Alliance, LLC

#===============================================================================
#
#         FILE: FlexLM_Parse.pm
#===============================================================================

use strict;
use warnings;

package FlexLM_Parse;
use Data::Dumper;

$Data::Dumper::Indent=1;
$Data::Dumper::Sortkeys=1;



sub new {
  my ($class, %args) = @_;
  return bless \%args, $class;
}

sub build_lm_data {
  my ($self, $arg_href) = @_;

  my $lm_stat_command = $arg_href->{lm_call};
  my $lm_lic_path = $arg_href->{lic_path};

  my $cmd_output = $self->call_lm_stat({lm_call=>$lm_stat_command});
  my $lm_db = $self->parse_lm_stat({lm_stat_output=>$cmd_output});
 
  #print "$lm_lic_path\n";
  if ($lm_lic_path ne 'None') {
  my $lic_href = $self->parse_lic_file({path=>$lm_lic_path});

  foreach my $app ( keys %{$lic_href}  ) {
    foreach my $attr ( keys %{$lic_href->{$app}{attr}}  ) {
      $lm_db->{app}{$app}{attr}{$attr} = $lic_href->{$app}{attr}{$attr};
    }
  }
  }
  return $lm_db;
}



sub call_lm_stat {
  my ($self, $arg_href) = @_;

  my $lm_call = $arg_href->{lm_call};
  my $lm_stat = `$lm_call`;
  
  return $lm_stat;
}


sub parse_lm_stat {
  my ($self, $arg_href) = @_;

  my $lm_href = {};
  my $product = $self->{name};
  
  my $lm_stat_output = $arg_href->{lm_stat_output};
  
  # get name of server / servers
  my ($servers) = $lm_stat_output =~ /^\s*(License\s+server\s+status.*?)\n/smi;
  my $servers_aref = parse_servers($servers, $product, $lm_href);
  $lm_href->{product}{$product}{attr}{servers} = $servers_aref;
  
  #Check the status of license servers
  my @server_stats = $lm_stat_output =~ /(\S+:\s+license\s+server\s+.*?)\n/msig;
  $lm_href->{product}{$product}{attr}{server_status} = \@server_stats;
  get_server_status($product, \@server_stats, $lm_href);


  #Parse app blocks (starts with Users of <APP>)
  my @app_blocks = $lm_stat_output =~ /(Users\s+of\s+\S+:.*?(?=Users\s+of\s+\S+:|$))/sig;
  
  foreach my $block ( @app_blocks ) {
    my ($app_name) = $block =~ /Users\s+of\s+(\S+):/i;
    
    #number of lics
    my ($total) = $block =~ /Total\s+of\s+(\S+)\s+licenses?\s+issued/i;
    $lm_href->{app}{$app_name}{attr}{total_lics} = $total;

    #Number of lics checked out
    my ($used) = $block =~ /Total\s+of\s+(\S+)\s+licenses?\s+in\s+use/i;
    $lm_href->{app}{$app_name}{attr}{used_lics} = $used;

    #See how many lics are used by each user
    my $cnt_href = tally_users($block);
    $lm_href->{app}{$app_name}{users} = $cnt_href;

    #Check for reserved lics
    my $res_href = tally_reserved($block);
    $lm_href->{app}{$app_name}{reserved} = $res_href if $res_href;
  }

  return $lm_href;
}

sub get_lic_count {
  my ($self, $arg_href) = @_;

  my $lic_blocks_aref = $arg_href->{blocks_aref};
  my $app = $arg_href->{app};
}

sub parse_servers {
  my $server_line = shift;
  my $product = shift;
  my $db_href = shift;
  
  my $server_aref = [];
  if ($server_line =~ /status:\s+\d+\@\S+(,\d+)?/) {
    my @port_n_servs = $server_line =~ /(\d+\@[^,]+)/g;
    #$server_aref = \@port_n_servs;
    
    foreach my $port_n_serv ( @port_n_servs ) {
      my ($port, $sname) = $port_n_serv =~ /(\d+)\@(\S+)/;
      $db_href->{product}{$product}{server}{$sname}{attr}{port} = $port;
      push @$server_aref, $sname;
    }
  }
  else {
    my ($server) = $server_line =~ /License\s+server\s+status:\s+(.*?)\n/;
    push @$server_aref, $server;
  }
  return $server_aref;
}

sub tally_users {
  my $lic_block = shift;

  my %users;
  my @users = $lic_block =~ /\n([ \t]+\S+.*?,\s+\d+\s+licenses)/ig;
  
  if (@users) {
    foreach my $user ( @users ) {
      my ($user_name) = $user =~ /^\s+(\S+)/;
      $user_name = lc($user_name);
      my ($lic_count) = $user =~ /,\s+(\d+)\s+licenses/;
      $users{$user_name}{attr}{count} += $lic_count;
    }
  }
  return \%users;
}


sub tally_reserved {
  my $lic_block = shift;

  my %reserved;
  my @ress = $lic_block =~ /\n([ \t]+\d+\s+RESERVATIONs\s+for\s+.*?)\n/ig;
  if (@ress) {
    foreach my $res ( @ress ) {
      my ($count, $res_name) = $res =~ /^[ \t]+(\d+)\s+RESERVATIONs\s+for\s+(.*?)\(/i;

      $res_name =~ s/\s+$//g;
      $res_name =~ s/\s+/_/g;
      $reserved{$res_name}{attr}{count} += $count;
    }
  }
  return \%reserved;
}



sub parse_lic_file {
  my ($self, $arg_href) = @_;

  my $lic_file_path = $arg_href->{path};

  my %APPS;

  open  my $lic_fh, '<', $lic_file_path or die  "$lic_file_path : $!\n";
  my $lic = do { local($/); <$lic_fh> };
  close $lic_fh;
  $lic =~ s/\s*\\\s*\n\s*/ /g;
  my @servers = $lic =~ /(^\s*SERVER.*?)\n/simg;

  my @features = $lic =~ /\n(feature.*?(?=\n\S+|$))/sig;
  my @incs = $lic =~ /\n(INCREMENT.*?(?=\n\S+|$))/sig;
  
  foreach my $feature ( @incs ) {
    my ($app, $expr) = $feature =~ /^INCREMENT\s+(\S+)\s+\S+\s+\S+\s+(\S+)/im;
    next if $app =~ /server_id/;
    if ($expr =~ /permanent/) {
      $APPS{$app}{attr}{expires} = 'never';
    }
    else {
      my $expr_formatted = _format_date($expr);
      $APPS{$app}{attr}{expires} = $expr_formatted; 
    }
  }

  foreach my $feature ( @features ) {
    my ($app, $expr) = $feature =~ /^FEATURE\s+(\S+)\s+\S+\s+\S+\s+(\S+)/im;
    if ($expr =~ /permanent/) {
      $APPS{$app}{attr}{expires} = 'never';
    }
    else {
      my $expr_formatted = _format_date($expr);
      $APPS{$app}{attr}{expires} = $expr_formatted; 
    }
  }

  return \%APPS;
}




sub _format_date {
  my $old = shift;

  my ($day, $month, $year) = $old =~ /^(\d+)\-(\S+)\-(\d+)/;
  #print "D $day\n";
  #print "M $month\n";
  #print "Y $year\n";

  if ($month =~ /jan/i) {
    $month = '01';
  }
  elsif ($month =~ /feb/i) {
    $month = '02';
  }
  elsif ($month =~ /mar/i) {
    $month = '03';
  }
  elsif ($month =~ /apr/i) {
    $month = '04';
  }
  elsif ($month =~ /may/i) {
    $month = '05';
  }
  elsif ($month =~ /jun/i) {
    $month = '06';
  }
  elsif ($month =~ /jul/i) {
    $month = '07';
  }
  elsif ($month =~ /aug/i) {
    $month = '08';
  }
  elsif ($month =~ /sep|sept/i) {
    $month = '09';
  }
  elsif ($month =~ /oct/i) {
    $month = '10';
  }
  elsif ($month =~ /nov/i) {
    $month = '11';
  }
  elsif ($month =~ /dec/i) {
    $month = '12';
  }

  return "$year-$month-$day";

}


sub get_server_status {
  my $product = shift;
  my $server_status_aref = shift;
  my $db_href = shift;

  my %serv;

  foreach my $server ( @$server_status_aref ) {
    my ($server_name) = $server =~ /^\s*(\S+):/;
    #print "SERVER NAME $server_name\n";
    if ($server =~ /license\s+server\s+UP/i) {
      $db_href->{product}{$product}{server}{$server_name}{attr}{status} = 'up';
    }
    else {
      $db_href->{product}{$product}{server}{$server_name}{attr}{status} = 'down';
    }
  }
  return $db_href;
}



1;


