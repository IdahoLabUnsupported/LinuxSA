#!/usr/bin/env python 
#    Copyright 2018 Battelle Energy Alliance, LLC
import subprocess 
import getpass
import argparse
import sys
import re
import textwrap
from argparse import RawTextHelpFormatter
import os
from passlib.hash import sha512_crypt

### Arguments ######################################################################################################################
parser = argparse.ArgumentParser(
    description='Hash password for linux',
    epilog=textwrap.dedent('''
        Examples:

        %(prog)s -s mysalt -l 16 
        %(prog)s -p secretpassword -r 60000 
        %(prog)s -w someword -p mypassword
        '''),
    formatter_class=RawTextHelpFormatter
)

parser.add_argument('-s', '--salt', help="User supplied salt")
parser.add_argument('-l', '--length_of_salt', default=8, help="Length of generated salt")
parser.add_argument('-p', '--password', help="Can supply a password, if not you will be prompted for one")
parser.add_argument('-r', '--rounds', default=10000,help="Permutations of input hash")
parser.add_argument('-w', '--word', help="Word to be hashed")

password = ""
gen_file = "/path/to/gen_pass.pyc"


if len(sys.argv)==1:
    parser.print_help()
    sys.exit(1)
args = parser.parse_args()

# If no password, prompt for one
if not (args.password):
    password = getpass.getpass('Please enter password to hash:').rstrip()
else:
    password = args.password


#Hash word
if args.name:
    password = subprocess.check_output(['python', gen_file, password, args.name]).rstrip()


if (args.salt):
    hash = sha512_crypt.encrypt(password, salt=args.salt, salt_size=args.length_of_salt, rounds=args.rounds)
else:
    hash = sha512_crypt.encrypt(password, salt_size=args.length_of_salt, rounds=args.rounds)


print(hash)

