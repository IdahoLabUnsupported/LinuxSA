#!/usr/bin/env python

#	Copyright 2018 Battelle Energy Alliance, LLC

import argparse
import sys
import re
import textwrap
from argparse import RawTextHelpFormatter
import ldap
import os
import subprocess

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../lib'))
import myldap

base_path = '/path/to/ingress.pyc'
gen_file = "/path/to/gen_pass.pyc"
base = subprocess.check_output(['python', base_path, '-o']).rstrip()
ldap_ingress = subprocess.check_output(['python', gen_file, base, 'HOSTNAME']).rstrip()


### Arguments ######################################################################################################################
parser = argparse.ArgumentParser(
    description='Run LDAP sanity checker script and give report on any issues found',
    epilog=textwrap.dedent('''
        Examples:
        %(prog)s
        '''),
    formatter_class=RawTextHelpFormatter
)

args = parser.parse_args()
##########################################################################################################################################

ldap_obj = myldap.MyLDAP()
conn = ldap_obj.manager_login(provided_passwd=ldap_ingress)
cur = ldap_obj.datawarehouse_login()


sp_all_dict = ldap_obj.sitepeople_all_2_dict()
sp_active_dict = ldap_obj.sitepeople_active_2_dict()

ifacts_dict = ldap_obj.get_ifacts_dict()

filters="(&(uid=*)(!(shadowExpire=0)))"
dn="ou=People,dc=my,dc=domain,dc=com"
searchScope=ldap.SCOPE_SUBTREE
entries = ldap_obj._MyLDAP__get_query(conn, filters, dn, searchScope)

QA_dict = {}
QA_dict['checks'] = {}

for entry in entries:
    uid = entry.uid
    name = entry.cn
    ### Build db
    if not 'users' in QA_dict['checks']: QA_dict['checks']['users'] = {}
    if not uid in QA_dict['checks']['users']: QA_dict['checks']['users'][uid] = {}
    
    if re.search(r'system.*account', name, re.I) is not None: continue
    if re.search(r'US|us', cc) is None: ldap_obj.check_user_for_current_security_plan(entry, ifacts_dict, QA_dict)
    ldap_obj.check_internal_in_sitepeople(entry, sp_all_dict, QA_dict)
    ldap_obj.check_fn_past_end_date(entry, QA_dict)
    ldap_obj.check_ldap_to_sitepeople_sync(entry, sp_all_dict, QA_dict)
    ldap_obj.check_ldap_attr_for_trailing_space(entry, QA_dict)
    ldap_obj.check_ldap_for_end_date(entry, QA_dict)
    ldap_obj.check_ldap_for_creation_date(entry, QA_dict)
    ldap_obj.check_for_unexpected_fields(entry, QA_dict)
    ldap_obj.check_uid_matches_dn(entry, QA_dict)
    ldap_obj.check_users_queue(entry, QA_dict)
    ldap_obj.check_for_missing_sponsor(entry, sp_active_dict, QA_dict)
    ldap_obj.check_uid_matches_gid(entry, QA_dict)

    ### Need Manager to check these
    ldap_obj.check_pwdChangedTime_matches_shadowLastChange(entry, QA_dict)
    ldap_obj.check_ldap_for_user_password(entry, QA_dict)
    ldap_obj.check_password_encryption_strength(entry, QA_dict)
    ldap_obj.check_password_not_more_than_6_months(entry, QA_dict, conn)

ldap_obj.find_users_with_failed_QA(QA_dict)
conn.unbind_s()


