#!/usr/bin/env python 

#	Copyright 2018 Battelle Energy Alliance, LLC

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../lib'))
import myldap


filters = 'objectclass=*'
dn = 'dc=my,dc=domain,dc=com'

ldap_obj = myldap.MyLDAP()


### LDAP1
conn = ldap_obj.anonymous_login()
ldap_dict = ldap_obj._get_query(conn, filters=filters, dn=dn)
### LDAP2 
conn2 = ldap_obj.anonymous_login(host='ldap://LDAPHOST')
ldap2_dict = ldap_obj._get_query(conn2, filters=filters, dn=dn)


### Compares ######################################################################
compare1 = ldap_obj.compare_ldap_structures('ldap', ldap_dict, 'ldap2', ldap2_dict)


if compare1 == 1:
    print("OK ldap ldap database is in sync with LDAP2")
    sys.exit(0)
else:
    message = 'CRITICAL '
    if compare1 == 0:
        message += "ldap database out of sync with ldap2\n"
    print(message)
    sys.exit(2)
