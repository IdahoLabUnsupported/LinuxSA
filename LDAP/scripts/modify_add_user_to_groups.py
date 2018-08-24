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

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../lib'))
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../SSH/lib'))
import myldap
import myssh

### Arguments ######################################################################################################################
parser = argparse.ArgumentParser(
    description='Add users to existing group',
    epilog=textwrap.dedent('''
        Examples:

        %(prog)s -u USERNAME -g group1 group2 group 3
        '''),
    formatter_class=RawTextHelpFormatter
)

parser.add_argument('-g', '--groups', nargs='+', help="Add space separated list for each group that user will be added to: -g group1 group2")
parser.add_argument('-u', '--user', help="username")


if len(sys.argv)==1:
    parser.print_help()
    sys.exit(1)
args = parser.parse_args()

if not (args.groups):
    parser.error('Must supply a group to which users will be added with -g or --groups')
if not (args.user):
    parser.error('Must supply a user to add to groups -u or --user')
##########################################################################################################################################

### Pass #####################################################################################
gen_file = "/path/to//gen_pass.pyc"
base_pass = getpass.getpass('Please Enter Password:')
ldap_pass = subprocess.check_output(['python', gen_file, base_pass, 'SERVER']).rstrip()
ldap_obj = myldap.MyLDAP()
conn = ldap_obj.manager_login(provided_passwd=ldap_pass)



groups = args.groups
user = args.user

for group in groups:
    group_entries = ldap_obj.group_search(conn, group, exact=1)
    if len(group_entries) !=1 :
        sys.exit("\n\nCould not find exactly one group with the name of {}!\n".format(group))
    group_entry_obj = group_entries[0]
    dn = group_entry_obj.dn
    print(dn)
    ldap_obj.add_to_ldap_list(conn, dn, user, user)
    



