#!/usr/bin/env python 

#	Copyright 2018 Battelle Energy Alliance, LLC

import argparse
import sys
import re
import textwrap
from argparse import RawTextHelpFormatter
import os
#import subprocess 
import getpass

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../lib'))
import myldap

### Arguments ######################################################################################################################
parser = argparse.ArgumentParser(
    description='Search LDAP accross the following attributes: cn, uidNumber, gidNumber, uid, telephoneNumber, employeeNumber, givenName, sn',
    epilog=textwrap.dedent('''
        Examples:

        lsearch USERNAME
        lsearch "myers*spencer"
        lsearch -s USERNAME
        lsearch -s spencer
        lsearch -n "spencer myers"
        lsearch -s USERNAME -u -e
        lsearch -b -s USERNAME
        lsearch -s USERNAME -w dns
        lsearch -g -s USERNAME
        lsearch '*'
        lsearch -a -s boise
        '''),
    formatter_class=RawTextHelpFormatter
)

search_group = parser.add_mutually_exclusive_group()
bind_group = parser.add_mutually_exclusive_group()
parser.add_argument('-a', '--active', action='store_true', help="Only print active users")
parser.add_argument('-b', '--brief', action='store_true', help="Turn on brief search or shortened version of output")
parser.add_argument('-c', '--csv', action='store_true', help="print query in csv format")
parser.add_argument('-e', '--email', action='store_true', help="Print email info for account renewal")
parser.add_argument('-w', '--where', help="Name of ldap server: default is ldap://LDAPSERVER")
search_group.add_argument('-s', '--search', help="String used for people search")
search_group.add_argument('-g', '--group', help="String used for group search")
search_group.add_argument('-n', '--name', help="First and last of person to search for in quotes: 'spencer myers'")
bind_group.add_argument('-u', '--user', action='store_true', help="Bind to LDAP as a user")
bind_group.add_argument('-m', '--manager', action='store_true', help="Bind to LDAP the manager")


if len(sys.argv)==1:
    parser.print_help()
    sys.exit(1)

if len(sys.argv)==2:
    orig = sys.argv[1]
    sys.argv.append(orig)
    sys.argv[1] = '-s'
    
args = parser.parse_args()
##########################################################################################################################################
where = ""
if not args.where:
    where = 'ldap://LDAPSERVER'
else:
    where = args.where
ldap_obj = myldap.MyLDAP()
ldap_server = ldap_obj.select_server(where)

conn = None
if args.manager:
    conn = ldap_obj.manager_login(host=ldap_server)
elif args.user:
    conn = ldap_obj.user_login(host=ldap_server)
else:
    conn = ldap_obj.anonymous_login(host=ldap_server)


if args.search:
    entries = ldap_obj.people_search(conn, args.search, active=args.active)
    if (args.csv):
        print(ldap_obj.print_csv(entries))
    elif (args.email):
        print(ldap_obj.print_email(entries))
    else:
        if args.brief:
            ldap_obj.print_brief_person_entries(conn, entries)
        else:
            ldap_obj.print_person_entries(conn, entries)
elif args.group:
    entries = ldap_obj.group_search(conn, args.group)
    ldap_obj.print_entries(entries)
elif args.name:
    name_search = re.search(r'(\S+)\s+(\S+)', args.name)
    first_name = name_search.group(1)
    last_name = name_search.group(2)
    entries = ldap_obj._MyLDAP__get_query(conn, '(cn=*{}*{}*)'.format(last_name, first_name))
    if args.brief:
        ldap_obj.print_brief_person_entries(conn, entries)
    else:
        ldap_obj.print_person_entries(conn, entries)


conn.unbind_s()
