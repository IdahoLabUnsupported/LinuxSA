#	Copyright 2018 Battelle Energy Alliance, LLC

#===============================================================================
#
#         FILE: Parse_LM_data.pm
#===============================================================================

use strict;
use warnings;
 
package Parse_LM_Data;
use Data::Dumper;
use Time::Local;

sub new {
  my ($class, %args) = @_;
  return bless \%args, $class;
}

sub print_app_data {
  my ($self, $arg_href) = @_;
  my $lm_href = $arg_href->{data};
  my $app_name = $arg_href->{name};


  my $out = "";
  my $app_href = $lm_href->{app}{$app_name};

  print "Could not find the app called --$app_name--" and return if not $app_href;

  $out .= print_header("Totals for $app_name");
  #printf("%-23s $app_href->{attr}{total_lics}\n", "Total Licenses:");
  #printf("%-23s $app_href->{attr}{used_lics}\n", "Used Licenses:");
  $out .= sprintf("%-23s $app_href->{attr}{total_lics}\n", "Total Licenses:");
  $out .= sprintf("%-23s $app_href->{attr}{used_lics}\n", "Used Licenses:");
  my $percent = sprintf("%.1f", $app_href->{attr}{used_lics} / $app_href->{attr}{total_lics} * 100 );
  #printf("%-23s $percent\n", "Percent Used:");
  $out .= sprintf("%-23s $percent\n", "Percent Used:");

  if (keys %{$app_href->{users}}) {
    $out .= print_header("User Licenses");
    foreach my $user (sort keys %{$app_href->{users}}  ) {
      #printf("%-12s has  %-3s licenses\n", $user, $app_href->{users}{$user}{attr}{count});
      $out .= sprintf("%-12s has  %-3s licenses\n", $user, $app_href->{users}{$user}{attr}{count});
    }
  }

  if (keys %{$app_href->{reserved}}) {
    $out .= print_header("Reserved Licenses");
    foreach my $res (sort keys %{$app_href->{reserved}}  ) {
      #printf("%-15s has reserved %-3s licenses\n", $res, $app_href->{reserved}{$res}{attr}{count});
      $out .= sprintf("%-15s has reserved %-3s licenses\n", $res, $app_href->{reserved}{$res}{attr}{count});
    }
  }
  $out .= "\n\n";
  return $out;
}


sub get_app_lic_usage {
  my ($self, $arg_href) = @_;
  my $lm_href = $arg_href->{data};
  my $app_name = $arg_href->{name};


  my $out = "";
  my $app_href = $lm_href->{app}{$app_name};

  print "Could not find the app called --$app_name--" and return if not $app_href;

  my $percent = sprintf("%.1f", $app_href->{attr}{used_lics} / $app_href->{attr}{total_lics} * 100 );
  return $percent, $app_href->{attr}{used_lics}, $app_href->{attr}{total_lics}
}



sub print_header {
  my $title = shift;

  my $header = "";
  my $title_len = length($title);
  my $max = 40;

  my $offset = $max - ($title_len + 2);

  #print "\n";
  #print "##########################################\n";
  #printf "#   $title%${offset}s\n", "#";
  #print "##########################################\n";

  $header .= "\n";
  $header .= "##########################################\n";
  $header .= sprintf "#   $title%${offset}s\n", "#";
  $header .= "##########################################\n";
  return $header;

}

sub get_days_to_expire {
  my ($self, $arg_href) = @_;

  my $lm_href = $arg_href->{data};
  my $app_name = $arg_href->{name};

  my $expire_date = $lm_href->{app}{$app_name}{attr}{expires};
  my $days_left = _get_days_to_expire($expire_date);
  return $days_left;
}

sub _get_days_to_expire {
  my $expire_date = shift;

  #print "ED $expire_date\n";
  # Get year month and day of expire
  my ($then_year, $then_month, $then_day) = split /\-/, $expire_date;
  # set hour to midnight
  my $then_seconds = 0;
  my $then_minutes = 0;
  my $then_hours = 0;

  # get locale time in epoch seconds
  my $time = time;


  # convert then time to epoch seconds
  my $time_then = timelocal($then_seconds, $then_minutes, $then_hours, $then_day,$then_month-1,$then_year);

  # Get just the whole number of days until lics expire
  my $days_difference = int(($time_then - $time) / 86400);
  return $days_difference;
}


sub check_servers_status {
  my ($self, $arg_href) = @_;
  my $lm_href = $arg_href->{data};
  my $product_name = $arg_href->{product};

  my $all_up = 1;
  my $found_servers = 0;
  my $data;

  foreach my $server (sort keys %{$lm_href->{product}{$product_name}{server}} ) {
    $found_servers = 1;
    if ($lm_href->{product}{$product_name}{server}{$server}{attr}{status} =~ /up/i) {
      $all_up &= 1;
      $data .= " $product_name on $server: licenses UP ";
    }
    else {
      $all_up &= 0;
      $data .= " $product_name on $server: licenses DOWN ";
    }
  }
  if ($all_up and $found_servers) {
    return 0, $data;
  }
  else {
    return 1, $data;
  }

}

sub check_for_servers {
  my ($self, $arg_href) = @_;
  my $lm_href = $arg_href->{data};
  my $product_name = $arg_href->{product};
  my $server_cnt = $arg_href->{server_cnt};

  my @servers = sort keys %{$lm_href->{product}{$product_name}{server}};
  my $found_servers = 0;
  my $down_cnt = 0;
  my $up_cnt = 0;
  my $data;

  foreach my $server ( @servers ) {
    if ($server) {
      $found_servers++;
      my $status = $lm_href->{product}{$product_name}{server}{$server}{attr}{status};
      if ($status =~ /up/i) {
        $data .= " $product_name on $server: licenses UP ";
        $up_cnt++;
      }
      else {
        $data .= " $product_name on $server: licenses DOWN ";
        $down_cnt++;
      }
    }
  }
  if ($server_cnt == 3) {
    if ($up_cnt <= 1) {
      $data .= "  Servers Down  ";
      return 2, $data;
    }
    elsif ($up_cnt == 2) {
      $data .= " One Server Down  ";
      return 1, $data;
    }
    else {
      return 0, $data;
    }
  }
  elsif ($server_cnt == 1) {
    if ($up_cnt != 1) {
      $data .= "  Server Down  ";
      return 2, $data;
    }
    else {
      return 0, $data;
    }
  }

  return 3, $data;
}





1;

