#!/usr/bin/env perl 
#===============================================================================
# 	 Copyright 2018 Battelle Energy Alliance, LLC
#         FILE: server_reports.pl
#      CREATED: 10/28/2015 01:44:42 PM
#     REVISION: ---
#===============================================================================

use strict;
use warnings;
use utf8;

use Parallel::ForkManager;
use Getopt::Long;
use Data::Dumper;

use File::FindLib 'general/Files_and_Dirs/lib';
use File::FindLib 'general/scripts';
use Files_and_Dirs;
use Net::OpenSSH;
use Term::ReadKey;
use Capture::Tiny;

my $max_processes = 40;
my $pm = Parallel::ForkManager->new($max_processes);

my $usage = "
USAGE: $0
--server <name of server> --server <other server>...  list servers one at a time
[--nofork] ()                                         turn forking off
--root                                                use root credentials (will be prompted for password)
--mounted                                             servers that have /home mounted on nfs
--update                                              servers that need patched with normal yum apt-get commands
--all                                                 blast to all servers
--passwd                                              change root password
--os                                                  use the servers that are in each OS
--cli                                                 command you want to run on servers (serparate by ;)
--scripts <path to script>  --script <path to script> List of scripts that you want to run                                          
";


my @servers;
my $fork = 1;
my $all = 0;
my $os = 0;
my $set_all = 0;
my $update = 0;
my $vm = 0;
my $root = 0;
my $debug = 0;
my $passwd = 0;
my $cli;
my @scripts;
my $tmp = '/path/to/tmp';

### ALL SERVERS #################################################
my @all_servers = qw( server1 server2 server3 ... );
my @rep_servers = qw( server1 server2 server3 ...);
################################################################

GetOptions (
  "servers=s"      => \@servers,
  "fork!"          => \$fork,
  "all!"           => \$all,
  "os!"            => \$os,
  "set_all!"       => \$set_all,
  "update!"        => \$update,
  "vm!"            => \$vm,
  "passwd!"        => \$passwd,
  "root!"          => \$root,
  "debug!"         => \$debug,

  "cli=s"          => \$cli,
  "scripts=s"      => \@scripts

) or die("Error in command line arguments\n");

### Build command to be run on servers 
my $cmd = "";
foreach my $script ( @scripts ) {
  $cmd .= " $script; ";
}
$cmd .= $cli if $cli;
#####################################
#print "CMD $cmd\n";
#print "CLI $cli\n";
if ($set_all) {
  print_all_hosts();
  exit;
}
$cmd = 1 if $passwd;
die "$usage" if not $cmd or $cmd =~ /^\s*$/;

@servers = @all_servers if $all;
@servers = @rep_servers if $os;

print "SERVER LIST @servers\n";
chomp(my $user = `whoami`);

my $ssh_user;
my $pass;
my $new_base;
my $change_pass;
$root = 1 if $passwd;

if ($root) {
  $ssh_user = 'root';
  print "\nPlease enter Password\n";
  ReadMode 'noecho';
  chomp ($pass = ReadLine 0);
  ReadMode 'normal';
  print "\n\n";
}
elsif ($all) {
  $ssh_user = $user;
  print "\nPlease enter your Password\n";
  ReadMode 'noecho';
  chomp ($pass = ReadLine 0);
  ReadMode 'normal';
  print "\n\n";
}
else {
  $ssh_user = $user;
}

if ($passwd) {
  $ssh_user = 'root';
  print "Enter New Password:";
  ReadMode('noecho');
  chomp($change_pass = ReadLine 0);
  print "\n";
  print "Please Re-enter Password:";
  chomp(my $pass2 = ReadLine 0);
  ReadMode(0);
  print "\n\n";
  die ("\n\nPasswords did not match!\n\n") if $change_pass ne $pass2;
}

my $gen_file = '/path/to/gen/file';

foreach my $server ( @servers ) {
  if ($fork) {
    $pm->start and next;
  }
  #print "Server $server\n";
  my $server_tmp = "$tmp/${server}_out.txt";
  if ($passwd) {
    chomp (my $new_change_pass = `$gen_file '$change_pass' $server`);
    my $salt = join '', ('.', '/', 0..9, 'A'..'Z', 'a'..'z')[rand 64, rand 64, rand 64, rand 64, rand 64, rand 64, rand 64, rand 64];
    my $change_pass_hash = crypt($new_change_pass, "\$6\$$salt\$");
    $change_pass_hash =~ s/\$/\\\$/g;
    $cmd = "echo root:$change_pass_hash | /usr/sbin/chpasswd -e";
  }
  chomp (my $new_pass = `$gen_file '$pass' $server`) if $root;

  open  my $out_fh, '>', $server_tmp or die  "$server_tmp $!\n";

  my $ssh;
  my ( $ssh_stdout, $ssh_stderr, @ssh_result ) = Capture::Tiny::capture {
    if ( $root ) {
      $ssh = Net::OpenSSH->new($server, user=>$ssh_user, password=>$new_pass );
    }
    elsif (not grep /^$server$/, @mounted_servers) {
      $ssh = Net::OpenSSH->new($server, user=>$ssh_user, password=>$pass );
    }
    else {
      $ssh = Net::OpenSSH->new($server, user=>$ssh_user );
    }
  };
  if ($debug) {
    print $out_fh "\n\nDEBUG:\nSTDOUT: $ssh_stdout\nSTDERR: $ssh_stderr\n\n";
  }

  my ($output, $err) = $ssh->capture2({ timeout => 10800 },  "$cmd");
  if ($ssh->error) {
    print $out_fh "$server: operation didn't complete successfully:\n";
    print $out_fh "STDOUT:\n$ssh_stdout\n\n" if $ssh_stdout;
    print $out_fh "STDERR:\n$ssh_stderr\n\n" if $ssh_stderr;
    print $out_fh "OUTPUT:\n$output\n\n" if $output;
    print $out_fh "STDERR:\n$err\n\n" if $err;
    die "Problem with $server; check output below\n";
  }
  
  print $out_fh "\nSTDERR: $err\n" if $err;
  print $out_fh "\nOUTPUT:\n$output";
  close  $out_fh;


  if ($fork) {
    $pm->finish;
  }
}


if ($fork) {
  $pm->wait_all_children;
}

print "\n\n";
foreach my $server ( @servers ) {
  my $server_tmp = "$tmp/${server}_out.txt";
  my $header = "#" x 80;
  print "$header\n";
  print "### SERVER: $server\n";
  print "$header\n";
  open  my $in_fh, '<', $server_tmp or die  "$server_tmp : $!\n";
  while (<$in_fh>) {
    print $_;
  }
  close  $in_fh;
  print "\n\n";
  system("rm $server_tmp");
}
