#!/usr/bin/env perl 

use strict;
use warnings;
use utf8;

use File::Glob qw( bsd_glob );

chomp(my $user = `whoami`);

my $home = "/home/$user";
my $git_links = "$home/git_links";

my @files = ( bsd_glob("$git_links/.*"), bsd_glob("$git_links/*") );
my $vim_swap = "$home/.vim/swap";


chdir $home;

foreach my $file ( @files ) {
  next if $file =~ /.*\/\.\.?$/;
  print "File $file\n";
  my ($file_name) = $file =~ /.*\/(.*)/;
  print "NAME $file_name\n";
  my $dest = "$home/$file_name";
  if (-e "$dest") {
    print "Moving $file_name to ${file_name}_orig\n";
    system("mv $dest ${dest}_orig");
  }
  print "Creating link from $file to $dest\n";
  system("ln -s $file $dest");
}

mkdir $vim_swap if not -d $vim_swap;


