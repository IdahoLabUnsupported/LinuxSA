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
import ldap
import time
import glob
import ldif

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../lib'))
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../SSH/lib'))
import myldap
import myssh

### Arguments ######################################################################################################################
parser = argparse.ArgumentParser(
    description="Restore user's ldap entries from archive",
    epilog=textwrap.dedent('''
        Examples:

        %(prog)s -u USERNAME
        '''),
    formatter_class=RawTextHelpFormatter
)

parser.add_argument('-u', '--userid', help="user's id like USERNAME")


if len(sys.argv)==1:
    parser.print_help()
    sys.exit(1)
args = parser.parse_args()

if not (args.userid):
    parser.error('Must supply a user id with -u or --userid')
##########################################################################################################################################


### Set varibles #########################################################################
userid = args.userid
gen_file = "/path/to//gen_pass.pyc"
ldif_dir = '/path/to/archive'
##########################################################################################


### Pass #####################################################################################
base_pass = getpass.getpass('Please Enter Password:')
ldap_pass = subprocess.check_output(['python', gen_file, base_pass, 'SERVER']).rstrip()
ldap_obj = myldap.MyLDAP()
conn = ldap_obj.manager_login(provided_passwd=ldap_pass)
##############################################################################################


### Restore each ldif file ###############################################
ldif_files = glob.glob("{}/{}/*importable*.ldif".format(ldif_dir, userid))
for LDIF in ldif_files:
    reader = ldif.LDIFRecordList(open(LDIF, "rb"))
    reader.parse()
    dn, entry = reader.all_records[0]
    ldif_content = ldap.modlist.addModlist(entry)
    ldap_obj.add_ldap_entry(conn, dn, ldif_content, userid)
