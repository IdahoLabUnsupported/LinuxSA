#!/usr/bin/env python

#	Copyright 2018 Battelle Energy Alliance, LLC

import argparse
import sys
import re
import textwrap
from argparse import RawTextHelpFormatter
import ldap
import os

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../lib'))
import myldap

ldap_obj = myldap.MyLDAP()
conn = ldap_obj.manager_login()

dn="ou=People,dc=my,dc=domain,dc=com"
filters="(&(uid=*)(!(shadowExpire=0)))"
searchScope=ldap.SCOPE_SUBTREE
attributes=["userPassword"]
entries = ldap_obj._MyLDAP__get_query(conn, filters, dn, searchScope, attributes)

totals_dict = {}
totals_dict['total'] = 1
for entry in entries:
    passwd = entry.userPassword
    ptype = re.match(r'{(.*?)}', passwd).group(1)
    ptype_lc = ptype.lower()
    totals_dict['total'] += 1
    if not ptype_lc in totals_dict:
        totals_dict[ptype_lc] = 1
    else:
        totals_dict[ptype_lc] += 1


print("\n")
print("{0: <10}: ".format('Total')),
print(totals_dict['total'])
for hash_type in totals_dict:
    if hash_type == 'total': continue
    percent = (float(totals_dict[hash_type]) / float(totals_dict['total'])) * 100
    print("{0: <10}: ".format(hash_type)),
    print("{0} ({1:0.2f}%)").format(totals_dict[hash_type], percent)

print("\n")

conn.unbind_s()
