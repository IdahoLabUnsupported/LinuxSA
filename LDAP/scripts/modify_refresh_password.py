#!/usr/bin/env python 

#	Copyright 2018 Battelle Energy Alliance, LLC

import argparse
import getpass
import sys
import textwrap
import subprocess
import re
from argparse import RawTextHelpFormatter
import os
import time
import ldap

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../lib'))
gen_file = "/path/to/gen_pass.pyc"
import myldap

### Arguments ############################################################
parser = argparse.ArgumentParser(
    description='Refresh system account password',
    epilog=textwrap.dedent('''
        Examples:

        %(prog)s -u USERNAME
        '''),
    formatter_class=RawTextHelpFormatter
)

parser.add_argument('-u', '--userid', help="user id like USERNAME")

if len(sys.argv)==1:
    parser.print_help()
    sys.exit(1)
args = parser.parse_args()

if not (args.userid):
    parser.error('Must supply a user id  with -i or --userid')

##########################################################################

### set variables ############################################################################
base_pass = getpass.getpass('Please Enter Password:')
ldap_pass = subprocess.check_output(['python', gen_file, base_pass, 'LDAPHOSTNAME']).rstrip()
##############################################################################################

### create ldap object #################################
ldap_obj = myldap.MyLDAP()
conn = ldap_obj.manager_login(provided_passwd=ldap_pass)
entries = ldap_obj.people_search(conn, args.userid, exact=1)
if len(entries) == 0:
    dn="ou=System,dc=my,dc=domain,dc=com"
    filters="uid={}".format(args.userid)
    searchScope=ldap.SCOPE_SUBTREE
    attributes=["+","*"]
    entries = ldap_obj._MyLDAP__get_query(conn, filters, dn, searchScope, attributes)
ldap_obj.check_for_more_than_one_entry(entries)
user_entry_obj = entries[0]
user_dn = user_entry_obj.dn
#user_cn = user_entry_obj.cn
old_pass = user_entry_obj.userPassword
#########################################################

### get password check it back in ################################################################
ldap_obj.modify_ldap_attribute(conn, user_dn, user_entry_obj, 'userPassword', old_pass, args.userid)
###################################################################################################
conn.unbind_s()
#del(ldap_obj)

#time.sleep(2)

ldap_obj2 = myldap.MyLDAP()
conn2 = ldap_obj2.manager_login(provided_passwd=ldap_pass)
entries2 = ldap_obj2.people_search(conn2, args.userid, exact=1)
system_flag = 0
if len(entries2) == 0:
    dn="ou=System,dc=my,dc=domain,dc=com"
    filters="uid={}".format(args.userid)
    searchScope=ldap.SCOPE_SUBTREE
    attributes=["+","*"]
    entries2 = ldap_obj._MyLDAP__get_query(conn2, filters, dn, searchScope, attributes)
    system_flag = 1
ldap_obj2.check_for_more_than_one_entry(entries2)
user_entry_obj2 = entries2[0]

days, passwd_slc = ldap_obj2.get_days_from_password_change(user_entry_obj2)

if system_flag == 1:
    conn2.unbind_s()
    sys.exit()

if hasattr(user_entry_obj2, 'shadowLastChange'):
    ldap_obj2.modify_ldap_attribute(conn2, user_dn, user_entry_obj2, 'shadowLastChange', str(passwd_slc), args.userid)
else:
    ldap_obj2.add_ldap_attribute(conn2, user_dn, 'shadowLastChange', str(passwd_slc), args.userid)
conn2.unbind_s()



