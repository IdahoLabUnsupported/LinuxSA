#!/usr/bin/env python 
# 	Copyright 2018 Battelle Energy Alliance, LLC
import subprocess 
import getpass
import argparse
import sys
import re
import textwrap
from argparse import RawTextHelpFormatter
import os
import base64

### Arguments ######################################################################################################################
parser = argparse.ArgumentParser(
    description='Encode or decode message in base64',
    epilog=textwrap.dedent('''
        Examples:

        %(prog)s -e encodethis 
        %(prog)s -d =base64string 
        %(prog)s 
        '''),
    formatter_class=RawTextHelpFormatter
)

group = parser.add_mutually_exclusive_group()

group.add_argument('-e', '--encode', action='store_true', help="Encode message")
group.add_argument('-d', '--decode', action='store_true', help="Decode message")
parser.add_argument('-m', '--message', help="message to be encoded or decoded")


if len(sys.argv)==1:
    parser.print_help()
    sys.exit(1)
args = parser.parse_args()

if args.encode and not args.message:    
    to_code = getpass.getpass('Please enter string to encode:').rstrip()
    coded = base64.b64encode(to_code)
    print(coded),
elif args.encode:
    coded = base64.b64encode(args.message)
    print(coded),
elif args.decode and not args.message:
    parser.print_help()
    sys.exit(1)
elif args.decode:
    decoded = base64.b64decode(args.message)
    print(decoded),
    
