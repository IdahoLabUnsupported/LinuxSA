#	Copyright 2018 Battelle Energy Alliance, LLC

#===============================================================================
#
#         FILE: Nagios.pm
#===============================================================================

use strict;
use warnings;
 
#package Nagios;

sub check_results {

  my $arg_href = shift;

  my $warn = $arg_href->{warn};
  my $crit = $arg_href->{critical};
  my $actual = $arg_href->{actual};
  my $type = $arg_href->{type};
  my $message = $arg_href->{message} || " ";
  my $data = $arg_href->{data} || " ";

  #print "WARN $warn\n";
  #print "CRIT $crit\n";
  #print "ACTUAL $actual\n";
  #print "Message $message\n";
  #print "Data $data\n";

  my $flag;

  if ($warn and not $crit) {
    if ($type =~ /left/i) {
      $flag = check_warn_left($warn, $actual);
    }
    elsif ($type =~ /used/i) {
      $flag = check_warn_used($warn, $actual);
    }
  }
  elsif ($warn and $crit) {
    if ($type =~ /left/i) {
      $flag = check_warn_crit_left($warn, $actual, $crit);
    }
    elsif ($type =~ /used/i) {
      $flag = check_warn_crit_used($warn, $actual, $crit);
    }
  }
  else {
    $flag = 3;
  }

  my ($return_code, $nagios_output) = print_nagios_return($flag, $message, $data);
  return $return_code, $nagios_output;
}

sub print_nagios_return {
  my $flag = shift;
  my $message = shift;
  my $data = shift;

  if ($flag == 0) {
    return 0, "$message OK - $data";
  }
  elsif ($flag == 1) {
    return 1, "$message Warning - $data"
  }
  elsif ($flag == 2) {
    return 2, "$message Critical - $data"
  }
  elsif ($flag == 3) {
    return 3, "$message Unknown - $data"
  }
}


sub check_warn_used {
  my $warn = shift;
  my $actual = shift;

  if (not $actual) {
    return 2;
  }

  if ( $actual >= $warn ) {
    return 1;
  }
  elsif ( $actual < $warn and $actual >= 0) {
    return 0;
  }
  else {
    return 3;
  }
}


sub check_warn_left {
  my $warn = shift;
  my $actual = shift;

  if (not $actual) {
    return 2;
  }

  
  if ( $actual <= $warn ) {
    return 1;
  }
  elsif ( $actual > $warn ) {
    return 0;
  }
  else {
    return 3;
  }
}

sub check_warn_crit_used {
  my $warn = shift;
  my $actual = shift;
  my $crit = shift;

  if (not $actual) {
    return 2;
  }


  if ( $actual >= $warn and $actual < $crit ) {
    return 1;
  }
  elsif ( $actual < $warn and $actual >= 0) {
    return 0;
  }
  elsif ($actual >= $crit) {
    return 2;
  }
  else {
    return 3;
  }
}

sub check_warn_crit_left {
  my $warn = shift;
  my $actual = shift;
  my $crit = shift;

  if (not $actual) {
    return 2;
  }

  
  if ( $actual <= $warn and $actual > $crit ) {
    return 1;
  }
  elsif ( $actual > $warn and $actual > $crit ) {
    return 0;
  }
  elsif ($actual <= $crit) {
    return 2;
  }
  else {
    return 3;
  }
}

1;
