#!/usr/bin/env python 

#	Copyright 2018 Battelle Energy Alliance, LLC

import argparse
import sys
import re
import textwrap
from argparse import RawTextHelpFormatter
import os

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../lib'))
import file_watch

### Arguments ######################################################################################################################
parser = argparse.ArgumentParser(
    description='Check for changes on file system',
    epilog=textwrap.dedent('''
        Examples:

        %(prog)s -s SERVER
        '''),
    formatter_class=RawTextHelpFormatter
)

parser.add_argument('-s', '--server', help="name of server you want to check")

if len(sys.argv)==1:
    parser.print_help()
    sys.exit(1)
args = parser.parse_args()

if not (args.server):
    parser.error('Must supply a server name with -s or --server')
##########################################################################################################################################
server = args.server




fw_obj = file_watch.FileWatch()
fw_obj.does_server_exist(server)
fw_obj.check_hosts_file_changes(hostname=server)

