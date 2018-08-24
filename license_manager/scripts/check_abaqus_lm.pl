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

my $common_name = "abaqus";
my $app_name = "abaqus";
my $lic_path = '/path/to/abaquslm.lic';
my $lm_call = "/path/to/lmstat -a -c $lic_path";
my $lm_servers_cnt = 3; #triad vs single


### Parse flex output ###
my $lm_obj = FlexLM_Parse->new(name=>$common_name);
my $lm_db = $lm_obj->build_lm_data({ lm_call=>$lm_call, lic_path=>$lic_path});

### Parse output ###
my $data_obj = Parse_LM_Data->new();

my ($rtn,$data) = $data_obj->check_for_servers({data=>$lm_db, product=>$common_name, server_cnt=>$lm_servers_cnt});
my ($return_code, $nagios_output) = print_nagios_return($rtn, "$common_name", $data);
print "$nagios_output\n";
exit $return_code;

