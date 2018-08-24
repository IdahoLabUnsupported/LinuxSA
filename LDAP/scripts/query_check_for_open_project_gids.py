#!/usr/bin/env python 

#	Copyright 2018 Battelle Energy Alliance, LLC

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../lib'))
import myldap

ldap_obj = myldap.MyLDAP()
conn = ldap_obj.anonymous_login()

next_gid = ldap_obj.check_for_open_gids(conn)
print("\n\nNext available gid for projects is: {}\n").format(next_gid)   
conn.unbind_s()
