#!/usr/bin/env python 

#	Copyright 2018 Battelle Energy Alliance, LLC

import os
import argparse
import getpass
import sys
import textwrap
from argparse import RawTextHelpFormatter
import subprocess
import re

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../lib'))
gen_file = "/path/to/gen_pass.pyc"
import myldap

### Arguments ############################################################
parser = argparse.ArgumentParser(
    description='Create LDAP project',
    epilog=textwrap.dedent('''
        This script will rename an RDN (relative domain name)
        for example:
        Change DN:uid=USERNAME a,ou=People,dc=my,dc=domain,dc=com
        to     DN:uid=USERNAME,ou=People,dc=my,dc=domain,dc=com

        Examples (Dont forget single quotes if there is a space):

        %(prog)s -u 'USER NAME' -r NEWUSERNAME'''),
    formatter_class=RawTextHelpFormatter
)

parser.add_argument('-u', '--userid', help="user id like USERNAME")
parser.add_argument('-r', '--rdn', help="new rdn i.e. new username")

if len(sys.argv)==1:
    parser.print_help()
    sys.exit(1)
args = parser.parse_args()

if not (args.userid):
    parser.error('Must supply a user id  with -i or --userid')
if not (args.rdn):
    parser.error('Must supply an attribute -r or --rdn')

##########################################################################

### set variables ############################################################################
base_pass = getpass.getpass('Please Enter Password:')
ldap_pass = subprocess.check_output(['python', gen_file, base_pass, 'LDAPHOSTNAME']).rstrip()
##############################################################################################

### create ldap object #################################
ldap_obj = myldap.MyLDAP()
conn = ldap_obj.manager_login(provided_passwd=ldap_pass)

entries = ldap_obj.people_search(conn, args.userid)
ldap_obj.check_for_more_than_one_entry(entries)
user_entry_obj = entries[0]
user_dn = user_entry_obj.dn

new_dn = user_dn[:]
new_dn = re.sub(args.userid, args.rdn, new_dn)
print("\n\nRenaming\n{}\nto\n{}\n").format(user_dn, new_dn)
conn.modrdn_s(user_dn, 'uid={}'.format(args.rdn), True)


