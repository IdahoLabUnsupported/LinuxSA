#!/usr/bin/env perl 
#===============================================================================
#	Copyright 2018 Battelle Energy Alliance, LLC
#         FILE: change_pass.pl
#
#        USAGE: ./change_pass.pl  
#
#  DESCRIPTION: 
#
#      OPTIONS: ---
# REQUIREMENTS: ---
#         BUGS: ---
#        NOTES: ---
#       AUTHOR: YOUR NAME (), 
# ORGANIZATION: 
#      VERSION: 1.0
#      CREATED: 08/03/2016 12:21:02 PM
#     REVISION: ---
#===============================================================================

use strict;
use warnings;
use utf8;


use Term::ReadKey;
use Data::Dumper;
use Crypt::SaltedHash;
use Try::Tiny;

print "New password:";
ReadMode('noecho');
chomp(my $new_base = ReadLine 0);
print "\n";
ReadMode(0);



my $salt = join '', ('.', '/', 0..9, 'A'..'Z', 'a'..'z')[rand 64, rand 64, rand 64, rand 64, rand 64, rand 64, rand 64, rand 64];
my $new = crypt($new_base, "\$6\$$salt\$");
print "$new\n\n\n";
$new =~ s/\$/\\\$/g;
#print "$new\n\n\n";

print "To change password use:\n";
print "echo <insert username here>:$new | /usr/sbin/chpasswd -e\n";
