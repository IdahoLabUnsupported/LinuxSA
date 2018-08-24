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

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../lib'))
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../RoboMail/lib'))
gen_file = "/path/to/gen_pass.pyc"
import myldap
import robo_mail

### Arguments ############################################################
parser = argparse.ArgumentParser(
    description='Create LDAP project',
    epilog=textwrap.dedent('''
        Examples:

        %(prog)s -u USERNAME
        %(prog)s -u USERNAME -c user.name@some.com not.real@email.com -t user.name@some.com not.real@email.com
        '''),
    formatter_class=RawTextHelpFormatter
)

parser.add_argument('-u', '--userid', help="user id like USERNAME")
parser.add_argument('-c', '--cc', nargs='+', help="Add space separated list for CC: -c some.name@some.com not.real@email.com")
parser.add_argument('-t', '--to', nargs='+', help="Add space separated list for TO: -t user.name@some.com not.real@email.com")

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
ldap_obj.check_for_more_than_one_entry(entries)
user_entry_obj = entries[0]
user_dn = user_entry_obj.dn
user_cn = user_entry_obj.cn
user_email = user_entry_obj.mail
first, last = ldap_obj.filter_name_parts(user_cn)
admin=getpass.getuser()
#########################################################


### Get random password hash ########################################################
new_pass, salted = ldap_obj.create_random_password_hash()
ldap_obj.modify_ldap_attribute(conn, user_dn, user_entry_obj, 'userPassword', salted, args.userid)
days, passwd_slc = ldap_obj.get_days_from_password_change(user_entry_obj)
#####################################################################################


### Set password reset to TRUE
ldap_obj.add_ldap_attribute(conn, user_dn, 'pwdReset', 'TRUE', args.userid)


if hasattr(user_entry_obj, 'shadowLastChange'):
    ldap_obj.modify_ldap_attribute(conn, user_dn, user_entry_obj, 'shadowLastChange', str(passwd_slc), args.userid)
else:
    ldap_obj.add_ldap_attribute(conn, user_dn, 'shadowLastChange', str(passwd_slc), args.userid)


### Get email signature #########################################
rmail_obj = robo_mail.RoboMail()
check = rmail_obj.is_person_in_db(admin)
if check == 0:
    admin = rmail_obj.get_username_for_reply_mail()
admin_email = rmail_obj.people['person'][admin]['attr']['email']
signature = rmail_obj.create_email_signature(admin)
#################################################################


### Email ######################################################
cc_list = rmail_obj.get_cc_list()
to_list = [user_email]
if args.cc:
    cc_list.extend(args.cc)
if args.to:
    to_list.extend(args.to)
uniq_cc = list(set(cc_list))
send_list = list(set(uniq_cc + to_list))

email_body = """
{},

I've given you the following temporary password:

{}

{}

""".format(first, new_pass, signature)
###############################################################

rmail_obj.send_mail(admin_email, to_list, uniq_cc, 'password reset', email_body)
conn.unbind_s()

