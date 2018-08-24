#!/usr/bin/env python 

#	Copyright 2018 Battelle Energy Alliance, LLC

import argparse
import sys
import re
import textwrap
from argparse import RawTextHelpFormatter
import os
import socket

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../lib'))
#import FileWatch
import file_watch

### Arguments ######################################################################################################################
parser = argparse.ArgumentParser(
    description='Add Changelog for file on system',
    epilog=textwrap.dedent('''
        Examples:

        %(prog)s -s servername -f /ect/something.conf
        '''),
    formatter_class=RawTextHelpFormatter
)

parser.add_argument('-s', '--server', help="name of server you want to check - Default is localhost")
parser.add_argument('-f', '--files', nargs='+', help="List of files you are checking in to changelog")
if len(sys.argv)==1:
    parser.print_help()
    sys.exit(1)
args = parser.parse_args()

if not (args.server):
    parser.error('Must supply a server name with -s or --server')
if not (args.files):
    parser.error('Must supply a file or list of files for which you want to write a changelog')
server = args.server
files = args.files

##########################################################################################################################################




fw_obj = file_watch.FileWatch()
fw_obj.does_server_exist(server)
fw_obj.update_change_log(files, server)

