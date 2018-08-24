#!/usr/bin/env perl 
#	Copyright 2018 Battelle Energy Alliance, LLC

use strict;
use warnings;
use utf8;


use lib '/path/to/license_managers/lib';
use lib '/path/to/nagios/lib';

use FlexLM_Parse;
use Parse_LM_Data;
use Nagios;

use Data::Dumper;
$Data::Dumper::Indent=1;
$Data::Dumper::Sortkeys=1;
use Getopt::Long;

my $usage = "
USAGE: $0 --warning <percent level>  ... percentage level where check will give warning\n
ex. $0 -w 90\n\n";
die $usage if $#ARGV < 0;

my $warning;
GetOptions (
  "warning=i" => \$warning,
) or die("Error in command line arguments\n");

die $usage if not $warning;

 
my $common_name = "abaqus";
my $app_name = "abaqus";
my $lic_path = '/path/to/abaquslm.lic';
my $lm_call = "/path/to/lmstat -a -c $lic_path";

### Parse flex output ###
my $lm_obj = FlexLM_Parse->new(name=>$common_name);
my $lm_db = $lm_obj->build_lm_data({ lm_call=>$lm_call, lic_path=>$lic_path});

### Parse output ###
my $data_obj = Parse_LM_Data->new();

my ($percent, $used, $total ) = $data_obj->get_app_lic_usage({data=>$lm_db, name=>$app_name});
my $data = "$percent percent of $common_name licenses: $used out of $total";
my ($return_code, $nagios_output) = check_results({type=>'used', warn=>$warning, message=>$common_name, actual=>$percent, data=>$data});
print "$nagios_output\n";
exit $return_code;

