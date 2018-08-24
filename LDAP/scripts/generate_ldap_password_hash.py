#!/usr/bin/env python 

#	Copyright 2018 Battelle Energy Alliance, LLC

import subprocess 
import getpass
import argparse
import sys
import re
import textwrap
from argparse import RawTextHelpFormatter
import os
import hashlib
from base64 import encodestring as encode
from base64 import decodestring as decode




sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../lib'))
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../SSH/lib'))
import myldap
import myssh

### Arguments ######################################################################################################################
parser = argparse.ArgumentParser(
    description='Create password hash that is LDAP compatible',
    epilog=textwrap.dedent('''
        Examples:

        %(prog)s -p secretpassword
        '''),
    formatter_class=RawTextHelpFormatter
)

parser.add_argument('-p', '--password', help="Password you would like to hash")


#def create_random_passord_hash(self, password):
def create_random_password_hash(password):
    new_pass = password[:]
    salt = os.urandom(4)
    hashed = hashlib.sha1(new_pass)
    hashed.update(salt)
    salted = "{SSHA}" + encode(hashed.digest() + salt)[:-1]
    return new_pass, salted



if len(sys.argv)==1:
    parser.print_help()
    sys.exit(1)
args = parser.parse_args()


new_pass, salted = create_random_password_hash(args.password)
print(new_pass, salted)
