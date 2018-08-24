#	Copyright 2018 Battelle Energy Alliance, LLC

import os
import getpass
import sys
import re
import ldap
import ldap.modlist as modlist
import time
import datetime
import smtplib
import mimetypes
import email
import email.mime.application
from   email.MIMEText import MIMEText
import hashlib
from   base64 import encodestring as encode
from   base64 import decodestring as decode
import random
import os
import ldif
import json
from   dateutil.relativedelta import relativedelta
import pycountry
import os.path
import psycopg2
import psycopg2.extras
import cPickle as pickle

sys.path.insert(0, "/path/to/RoboMail/lib")
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../SSH/lib'))
import myssh
import robo_mail



class Continue1(Exception):
    pass


class MyLDAP(object):

    ############################ LOGIN STUFF ###########################
    def __init__(self):
        self.gid_low = LOWGID
        self.gid_high = HIGID
        self.home_storage = 'STORAGEADDRESS:/STORAGEMNT'
        self.scratch_storage = '/SCRATCHMNT'
        self.new_user_doc_dir = '/doc/dir'
        self.ldap_mod_log_dir = '/ldap_mod_dir'
        self.mail_host = 'MAILHOST'
        self.password_expire_days = 200


    def anonymous_login(self, host="ldap://LDAPADDRESS"):
        conn = ldap.initialize(host)
        try:
            conn.protocol_version = ldap.VERSION3
            conn.simple_bind_s()
        except ldap.LDAPError, e:
            if type(e.message) == dict and e.message.has_key('desc'):
                print(e.message['desc'])
            else: 
                print(e)
                sys.exit(0)
        return conn


    def user_login(self, host="ldap://LDAPADDRESS", root_dn='uid={},ou=People,dc=your,dc=domain,dc=com'.format(getpass.getuser()), cacert_file='/path/to/cacert.pem', provided_passwd=""):
        if provided_passwd == "":
            passwd = getpass.getpass('Please enter ldap user password:').rstrip()
        else:
            passwd = provided_passwd
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
        ldap.set_option(ldap.OPT_X_TLS_CACERTFILE,cacert_file)
        conn = ldap.initialize(host)
        try:
            conn.start_tls_s()
            conn.protocol_version = ldap.VERSION3
            conn.simple_bind_s(root_dn, passwd)
        except ldap.LDAPError, e:
            if type(e.message) == dict and e.message.has_key('desc'):
                print(e.message['desc'])
                sys.exit(0)
            else: 
                print(e)
                sys.exit(0)
        return conn


    def manager_login(self, host="ldap://LDAPADDRESS", root_dn='cn=Manager,dc=your,dc=domain,dc=com', cacert_file='/path/to/cacert.pem', provided_passwd=""):
        if provided_passwd == "":
            passwd = getpass.getpass('Please enter MANAGER password:').rstrip()
        else:
            passwd = provided_passwd
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
        ldap.set_option(ldap.OPT_X_TLS_CACERTFILE,cacert_file)
        conn = ldap.initialize(host)
        try:
            conn.start_tls_s()
            conn.protocol_version = ldap.VERSION3
            conn.simple_bind_s(root_dn, passwd)
        except ldap.LDAPError, e:
            if type(e.message) == dict and e.message.has_key('desc'):
                print(e.message['desc'])
                sys.exit(0)
            else: 
                print(e)
                sys.exit(0)
        return conn


    ############################################################################################################################################


    def print_entries(self, entries):
        for entry in entries:
            entry.print_entry()
            print("\n")
        return(0)
    

    def _get_query(self, conn, filters, dn='dc=your,dc=domain,dc=com', searchScope=ldap.SCOPE_SUBTREE, attributes=["+","*"]):
        filters = re.sub(r'\*+', '*', filters)
        try:
            ldap_result_id = conn.search(dn, searchScope, filters, attributes)
            result_set=[]
            result_dict = {}
            while 1:
                result_type, result_data = conn.result(ldap_result_id, 0)
                #print(result_type)
                if (result_data == []):
                    break
                else:
                    if result_type == ldap.RES_SEARCH_ENTRY:
                        key = result_data[0][0]
                        #print(key)
                        result_dict[key] = dict(result_data[0][1])
        except ldap.LDAPError, e:
            print(e)
        return result_dict


    def __get_query(self, conn, filters, dn='dc=your,dc=domain,dc=com', searchScope=ldap.SCOPE_SUBTREE, attributes=["+","*"]):
        filters = re.sub(r'\*+', '*', filters)
        try:
            ldap_result_id = conn.search(dn, searchScope, filters, attributes)
            #print(ldap_result_id)
            result_set=[]
            while 1:
                result_type, result_data = conn.result(ldap_result_id, 0)
                if (result_data == []):
                    break
                else:
                    if result_type == ldap.RES_SEARCH_ENTRY:
                        #print(result_type, result_data)
                        #print(ldap.RES_SEARCH_ENTRY)
                        #print(result_data)
                        ldap_result_obj = LdapResults(result_data)
                        #print(ldap_result_obj)
                        result_set.append(ldap_result_obj)
                        #result_set.append(result_data)
                        #ldap_result_obj = LDAPEntry
        except ldap.LDAPError, e:
            print(e)
        return result_set


    def print_to_user_log(self, user_uid, text):
        date = time.strftime('%Y-%m-%d-%H:%M:%S').rstrip()
        log_dir = self.ldap_mod_log_dir
        user_dir = "{}/{}".format(log_dir, user_uid)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        log_path = "{}/{}_ldap_modifications.log".format(user_dir, user_uid)
        try:
            with open(log_path, "a") as log_fh:
                log_fh.write("[{}]    {}".format(date, text))
        except:
            with open(backup_log_path, "a") as log_fh2:
                log_fh2.write("[{}]    {}".format(date, text))

        


    #### MODIFY ATTRIBUTES ##########################################################################            
    def modify_ldap_attribute(self, conn, dn, entry, attribute, new_val, uid):
        try:
            old_val = getattr(entry, attribute)
            mod_attrs = [( ldap.MOD_REPLACE, attribute, new_val )]
            conn.modify_s(dn, mod_attrs)
            print("\nModifying '{}' from '{}' to '{}' for '{}'\n").format(attribute, old_val, new_val, dn)
            text = ""
            if attribute == 'userPassword':
                text = "Modifying '{}' from old password to new password for '{}'\n".format(attribute, dn)
            else:
                text = "Modifying '{}' from '{}' to '{}' for '{}'\n".format(attribute, old_val, new_val, dn)
            self.print_to_user_log(uid, text)

        except ldap.LDAPError, e:
            print("\nERROR Modifying '{}' from '{}' to '{}' for '{}'\n").format(attribute, old_val, new_val, dn)
            print(e)
        return(0)


    def add_ldap_attribute(self, conn, dn, attribute, new_val, uid):
        try:
            mod_attrs = [( ldap.MOD_ADD, attribute, new_val )]
            conn.modify_s(dn, mod_attrs)
            print("\nSetting attribute: '{}' to '{}' for '{}'\n").format(attribute, new_val, dn)
            text = "Setting attribute: '{}' to '{}' for '{}'\n".format(attribute, new_val, dn)
            self.print_to_user_log(uid, text)

        except ldap.LDAPError, e:
            print("\nSetting attribute: '{}' to '{}' for '{}'\n").format(attribute, new_val, dn)
            print("\nERROR adding attribute: '{}' to '{}' for '{}'\n").format(attribute, new_val, dn)
            print(e)
        return(0)


    def delete_ldap_attribute(self, conn, dn, attribute, uid):
        try:
            print("\nRemoving attribute: '{}' from '{}'\n").format(attribute, dn)
            mod_attrs = [( ldap.MOD_DELETE, attribute, None)]
            conn.modify_s(dn, mod_attrs)
            text = "Removing attribute: '{}' from '{}'\n".format(attribute, dn)
            self.print_to_user_log(uid, text)

        except ldap.LDAPError, e:
            print("\nERROR deleting attribute: '{}' from '{}'\n").format(attribute, dn)
            print(e)
        return(0)


    def delete_ldap_entry(self, conn, dn, uid):
        try:
            print("\nDeleting Entry: '{}'\n").format(dn)
            conn.delete_s(dn)
            text = "Deleting Entry: '{}'\n".format(dn)
            self.print_to_user_log(uid, text)

        except ldap.LDAPError, e:
            print("\nERROR Deleting Entry: '{}'\n").format(dn)
            print(e)
        return(0)


    def add_ldap_entry(self, conn, dn, ldif, uid):
        try:
            print("\nAdding entry to '{}'\n").format(dn)
            conn.add_s(dn, ldif)
            text = "Adding Entry: '{}'\n".format(dn)
            self.print_to_user_log(uid, text)

        except ldap.LDAPError, e:
            print("\nERROR adding new entry'{}': '{}'\n").format(dn, ldif)
            print(e)
        return(0)


    def add_to_ldap_list(self, conn, dn, attr, uid, list_name='memberUid'):
        try:
            print("\nAdding {} to {} {}\n").format(attr, dn, list_name)
            mod_list = []
            mod_list.append((ldap.MOD_ADD, list_name, attr ))
            conn.modify_s(dn, mod_list)
            text = "Adding {} to {} {}\n".format(attr, dn, list_name)
            self.print_to_user_log(uid, text)
        except ldap.LDAPError, e:
            print("\nERROR adding {} to {} {}\n").format(attr, dn, list_name)
            print(e)
        return(0)


    def remove_from_ldap_list(self, conn, dn, attr, uid, list_name='memberUid'):
        try:
            print("\nRemoving {} from {} {}\n").format(attr, dn, list_name)
            mod_list = []
            mod_list.append((ldap.MOD_DELETE, list_name, attr ))
            conn.modify_s(dn, mod_list)
            text = "Removing {} from {} {}\n".format(attr, dn, list_name)
            self.print_to_user_log(uid, text)
        except ldap.LDAPError, e:
            print("\nERROR removing {} from {} {}\n").format(attr, dn, list_name)
            print(e)
        return(0)



    ####################################################################################################


    def create_project_group(self, conn, project_name, gid_provided=None):
        gid = ""
        if gid_provided != None:
            gid = gid_provided
        else:
            gid = self.check_for_open_gids(conn)
        self.create_group(conn, project_name, gid)
        self.create_project_automount(conn, project_name)
        return gid


    def check_for_open_gids(self, conn, dn='dc=your,dc=domain,dc=com'):
        results = self.__get_query(conn, '(gidNumber=*)', attributes=['gidNumber'])
        gids = []
        for entry in results:
            gid = int(entry.gidNumber)
            if  self.gid_low <= gid <= self.gid_high:
                gids.append(gid)
        gids = sorted(set(gids))
        next_gid = self.find_next_gid(gids)
        return next_gid;


    def find_next_gid(self, gid_list):
        cnt = 0
        for i in range(self.gid_low, self.gid_high):
            if gid_list[cnt] != i:
                return i
            cnt+=1
        sys.exit("Could not find a gid number between {} and {}".format(self.gid_low, self.gid_high))


    def create_group(self, conn, group_name, gid):
        dn = "cn={},ou=Group,dc=your,dc=domain,dc=com".format(group_name)
        attrs = {}
        attrs['objectclass'] = ['person', 'posixGroup', 'top']
        attrs['sn'] = group_name
        attrs['cn'] = group_name
        attrs['gidNumber'] = str(gid)
        ldif = modlist.addModlist(attrs)
        self.add_ldap_entry(conn, dn, ldif, group_name)
        return(0)


    def create_project_automount(self, conn, project_name):
        dn = "automountKey={},automountMapName=auto.projects,dc=your,dc=domain,dc=com".format(project_name)
        automount = "{0}/projects/{1}".format(self.home_storage, project_name)
        attrs = {}
        attrs['objectclass'] = ['automount']
        attrs['automountKey'] = project_name
        attrs['automountInformation'] = automount
        ldif = modlist.addModlist(attrs)
        self.add_ldap_entry(conn, dn, ldif, project_name)
        return(0)


    def create_person_home_automount(self, conn, username, home_dir):
        dn = "automountKey={0},automountMapName=auto.home,dc=your,dc=domain,dc=com".format(username)
        automount = "{0}/{1}/{2}".format(self.home_storage, home_dir, username)
        attrs = {}
        attrs['objectclass'] = ['automount']
        attrs['automountKey'] = username
        attrs['automountInformation'] = automount
        ldif = modlist.addModlist(attrs)
        self.add_ldap_entry(conn, dn, ldif, username)
        return(0)


    def create_person_scratch_automount(self, conn, username):
        dn = "automountKey={0},automountMapName=auto.scratch,dc=your,dc=domain,dc=com".format(username)
        automount = "{0}/{1}".format(self.scratch_storage, username)
        attrs = {}
        attrs['objectclass'] = ['automount']
        attrs['automountKey'] = username
        attrs['automountInformation'] = automount
        ldif = modlist.addModlist(attrs)
        self.add_ldap_entry(conn, dn, ldif, username)
        return(0)


    def uid_search(self, conn, search_term, exact=0, active=0, searchScope=ldap.SCOPE_SUBTREE):
        search_dn = "ou=People,dc=your,dc=domain,dc=com";
        filters="";
        if exact:
            if active:
                filters = "(&((uid={0}))(!(shadowExpire=0)))".format(search_term)
            else:
                filters = "(uid={0})".format(search_term)
        else:
            if active:
                filters = "(&((uid=*{0}*)))(!(shadowExpire=0)))".format(search_term)
            else:
                filters = "(uid=*{0}*)".format(search_term)
        entries = self.__get_query(conn, filters, dn=search_dn, searchScope=searchScope)
        return entries


    def people_search(self, conn, search_term, exact=0, active=0, searchScope=ldap.SCOPE_SUBTREE):
        search_dn = "ou=People,dc=your,dc=domain,dc=com";
        filters="";
        if exact:
            if active:
                filters = "(&(|(cn={0})(uidNumber={0})(gidNumber={0})(uid={0})(telephoneNumber={0})(employeeNumber={0})(givenName={0})(sn={0}))(!(shadowExpire=0)))".format(search_term)
            else:
                filters = "(|(cn={0})(uidNumber={0})(gidNumber={0})(uid={0})(telephoneNumber={0})(employeeNumber={0})(givenName={0})(sn={0}))".format(search_term)
        else:
            if active:
                filters = "(&(|(cn=*{0}*)(uidNumber={0})(gidNumber={0})(uid=*{0}*)(telephoneNumber=*{0}*)(employeeNumber=*{0}*)(givenName=*{0}*)(sn=*{0}*))(!(shadowExpire=0)))".format(search_term)
            else:
                filters = "(|(cn=*{0}*)(uidNumber={0})(gidNumber={0})(uid=*{0}*)(telephoneNumber=*{0}*)(employeeNumber=*{0}*)(givenName=*{0}*)(sn=*{0}*))".format(search_term)
        entries = self.__get_query(conn, filters, dn=search_dn, searchScope=searchScope)
        return entries


    def group_search(self, conn, search_term, exact=0):
        search_dn = "ou=Group,dc=your,dc=domain,dc=com";
        filters="";
        if exact:
            filters = "(|(cn={0})(gidNumber={0})(sn={0}))".format(search_term)
        else:
            filters = "(|(cn=*{0}*)(gidNumber={0})(sn=*{0}*))".format(search_term)
        entries = self.__get_query(conn, filters, dn=search_dn)
        return entries


    def project_search(self, conn, search_term, exact=0):
        search_dn = 'automountMapName=auto.projects,dc=your,dc=domain,dc=com';
        filters="";
        if exact:
            filters = "(|(entryDN={0})(automountKey={0})(automountInformation={0}))".format(search_term)
        else:
            filters = "(|(entryDN=*{0}*)(automountKey=*{0}*)(automountInformation=*{0}*))".format(search_term)
        entries = self.__get_query(conn, filters, dn=search_dn)
        return entries


    def home_search(self, conn, search_term, exact=0):
        search_dn = "automountMapName=auto.home,dc=your,dc=domain,dc=com"
        if exact:
            filters = "(|(entryDN={0})(automountKey={0})(automountInformation={0}))".format(search_term)
        else:
            filters = "(|(entryDN=*{0}*)(automountKey=*{0}*)(automountInformation=*{0}*))".format(search_term)
        entries = self.__get_query(conn, filters, dn=search_dn)
        return entries


    def scratch_search(self, conn, search_term, exact=0):
        search_dn = "automountMapName=auto.scratch,dc=your,dc=domain,dc=com"
        if exact:
            filters = "(|(entryDN={0})(automountKey={0})(automountInformation={0}))".format(search_term)
        else:
            filters = "(|(entryDN=*{0}*)(automountKey=*{0}*)(automountInformation=*{0}*))".format(search_term)
        entries = self.__get_query(conn, filters, dn=search_dn)
        return entries


    def get_users_groups(self, conn, userid, dn="dc=your,dc=domain,dc=com", searchScope=ldap.SCOPE_SUBTREE, attributes=["+","*"]):
        filters="(&(cn=*)(memberUid={}))".format(userid)
        entries = self._get_query(conn, filters, dn, searchScope, attributes)
        
        group_list = []
        for dn in entries:
            cn = entries[dn]['cn'][0]
            group_list.append(cn)
        return group_list


    def check_for_more_than_one_entry(self, entries):
        if len(entries) != 1:
           print("Number of entries returned by query was not exactly 1")
           for entry in entries:
                print(entry[0][0])
           sys.exit()
        return(0)


    def filter_name_parts(self, name):
        parts = []
        name = re.sub(r'\s+I+\s*,', ',', name)
        if re.search(r'(^\S+\s+\S+),(.*)', name) is not None:
            one, two = re.search(r'(^\S+\s+\S+),.*?(\S+)', name).group(1,2)
            return two, one
        else:
            parts = re.split('\s+', name)
        new_name = []
        for part in parts:
            if re.search(r"\(|\)", part) is not None:
                next
            elif re.search(r"\.", part) is not None:
                next
            elif re.search(r"^\S$", part) is not None:
                next
            elif re.search(r"^i{1,}$", part, re.I) is not None:
                next
            else:
                new_name.append(part)
        sorted_names = []
        found_commas = list(filter(lambda x:re.search(r',', x), new_name))
        if list(filter(lambda x:re.search(r',', x), new_name)):
            cnt = 0
            for new in new_name:
                if re.search(",", new) is not None:
                    new = re.sub(',',"", new)
                    sorted_names.append(new_name[cnt+1])
                    sorted_names.append(new)
                    break
                cnt+=1
        else:
            sorted_names = new_name

        name_cnt = len(sorted_names)
        last = sorted_names[-1]
        first = ""
        if name_cnt == 0:
            first = ""
        else:
            first = sorted_names[0]
        return(first, last)
                    

    def get_sponsor_entry(self, conn, sponsor_name):
        first, last = self.filter_name_parts(sponsor_name)
        filters = "(cn=*{}*{}*)".format(last,first)
        dn = "ou=People,dc=your,dc=domain,dc=com"
        entry = self.__get_query(conn, filters, dn)
        if len(entry) != 1:
            print("Could not find sponsor using filter {}".format(sponsor_name))
            sponsor_name = raw_input("Please input sponsor name (Between quotes, last name first like 'Banner, Bruce'): ")
            sponsor_email = raw_input("Please input sponsor email: ")
            fake_entry = [[]]
            fake_entry[0].append(dn)
            fake_entry[0].append({'cn':[sponsor_name], 'mail':[sponsor_email], 'dn':[dn]})
            ldap_result_obj = LdapResults(fake_entry)
            return_list = []
            return_list.append(ldap_result_obj)
            return return_list
        return entry


    def strip_whitespace_from_field_ends(self, conn, entry):
        dn = entry.dn
        uid = entry.uid
        for attribute in sorted(vars(entry)):
            attr_val = getattr(entry, attribute)
            if isinstance(attr_val, str):
                val = attr_val
                if re.search(r'\s+$', val) is not None:
                    stripped_val = re.sub(r'\s+$', "", val)
                    print('Found an entry with whitespace at the end')
                    print('Changing --{}-- to --{}--'.format(val, stripped_val))
                    self.modify_ldap_attribute(conn, dn, entry, attribute, stripped_val, uid)

    
    def get_single_attribute(self, entries, attribute):
        entry_cnt = len(entries)
        if entry_cnt != 1:
            print("Tried to get attribute: {} from entries but the number of entries was not exactly 1").format(attribute)
            return(1)
        else:
            entry = entries[0]
            attr = getattr(entry, attribute)
            return attr


    def print_person_entries(self, conn, entries):
        for entry in entries:
            self.print_person_entry(conn, entry)
            print("")


    def print_person_entry(self, conn, entry):
        self.get_scratch_dir(conn, entry)
        self.get_home_dir(conn, entry)
        if hasattr(entry, 'pwdChangedTime'):
            days, passwd_slc = self.get_days_from_password_change(entry)
            if hasattr(entry, 'shadowMax'):
                days_to_pass_expire = int(entry.shadowMax) - days
                setattr(entry, 'passwordExpireDays', days_to_pass_expire)
        if hasattr(entry, 'accountEndDate'):
            expire_days = self.get_account_expiration(entry)
            setattr(entry, 'daysUntilExpire', expire_days)
        print('#' * 70)
        print("###  DN: {}").format(entry.dn)
        print('#' * 70)
        for attribute in sorted(vars(entry)):
            print("{0:<25}").format(attribute),
            if isinstance(attribute, list):
                for val in attribue:
                    print("{}").format(val),
            else:
                if attribute == 'pwdAccountLockedTime':
                    print("{} LOCKED").format(getattr(entry, attribute))
                else:
                    print(getattr(entry, attribute))


    def print_brief_person_entries(self, conn, entries):
        for entry in entries:
            self.print_brief_person_entry(conn, entry)
            print("")


    def print_brief_person_entry(self, conn, entry):
        self.get_scratch_dir(conn, entry)
        self.get_home_dir(conn, entry)
        if hasattr(entry, 'accountEndDate'):
            expire_days = self.get_account_expiration(entry)
            setattr(entry, 'daysUntilExpire', expire_days)
        print('#' * 70)
        print("###  DN: {}").format(entry.dn)
        print('#' * 70)
        for attribute in sorted(vars(entry)):
            if re.search(r'^cn$|^uid$|employeeNumber|telephoneNumber', attribute) is None:
                continue;
            else:
                print("{0:<25}").format(attribute),
                if isinstance(attribute, list):
                    for val in attribue:
                        print("{}").format(val),
                else:
                    if attribute == 'pwdAccountLockedTime':
                        print("{} LOCKED").format(getattr(entry, attribute))
                    else:
                        print(getattr(entry, attribute))


    def get_account_expiration(self, entry):
        if hasattr(entry, 'accountEndDate'):
            yyyymmdd=self.parse_end_date(entry)
            days_to_expire = self.get_days_to_expire(yyyymmdd)
            return days_to_expire
        return None


    def get_days_from_password_change(self, entry):
        pass_timestamp = ""
        if hasattr(entry, 'pwdChangedTime'):
            pass_timestamp = entry.pwdChangedTime
            pass_timestamp = re.sub(r'(^\d{4})(\d{2})(\d{2}).*', r'\1-\2-\3', pass_timestamp)
        else:
            pass_timestamp = '1990-01-01'
        #print(pass_timestamp)
        days_to_expire = self.get_days_from_expire(pass_timestamp)
        password_change_date = self.parse_date_for_datetime(pass_timestamp)
        epoch_days_since_change = (password_change_date - datetime.datetime(1970,1,1).date()).days
        return days_to_expire, epoch_days_since_change


    def parse_end_date(self, entry):
        if hasattr(entry, 'accountEndDate'):
            expire_date = entry.accountEndDate
            yyyymmdd = re.search(r'(\d+-\d+-\d+)', expire_date).group(1)
            return yyyymmdd
        else:
            return time.strftime('%Y-%m-%d').rstrip()
       

    def parse_password_timestamp(self, entry):
        pass_timestamp = ""
        if hasattr(entry, 'pwdChangedTime'):
            pass_timestamp = entry.pwdChangedTime
            pass_timestamp = re.sub(r'(^\S{4})(\S{2})(\S{})', '\1-\2-\3', passtimestamp)
        else:
            pass_timestamp = '1900-01-01'
        yyyymmdd = re.search(r'(\d+-\d+-\d+)', pass_timestamp).group(1)
        return yyyymmdd


    def get_days_to_expire(self, expire_date):
        today = datetime.date.today()
        then = self.parse_date_for_datetime(expire_date)
        diff = then - today
        return diff.days


    def get_days_from_expire(self, expire_date):
        today = datetime.date.today()
        then = self.parse_date_for_datetime(expire_date)
        diff = today - then
        return diff.days


    def parse_date_for_datetime(self, ldap_date):
        match = re.search(r'(.*?)-(.*?)-(.*)', ldap_date)
        then_year = int(match.group(1))
        then_month = int(match.group(2))
        then_day = int(match.group(3))
        then = datetime.date(then_year, then_month, then_day)
        return then


    def password_time_to_mst(self, ldap_passwd_change):
        tz_info = timezone('MST')
        time = re.sub(r'Z', '000', ldap_passwd_change)
        iso_8601_dt = dt.datetime.strptime(time, '%Y%m%d%H%M%S%f')
        mst_time = str(iso_8601_dt.replace(tzinfo=timezone('UTC')).astimezone(tz_info))
        return mst_time


    def get_scratch_dir(self, conn, entry):
        uid = entry.uid
        scratch_entries = self.scratch_search(conn, uid, 1)
        if len(scratch_entries) >= 1:
            scratch_attr = self.get_single_attribute(scratch_entries, 'automountInformation')
            if re.search(r'(\S+:/?/.*)', scratch_attr):
                scratch_dir = re.search(r'(\S+:/?/.*)', scratch_attr).group(1)
                setattr(entry, 'automountScratch', scratch_dir)
        return entry


    def get_home_dir(self, conn, entry):
        uid = entry.uid
        home_entries = self.home_search(conn, uid, 1)
        if len(home_entries) >= 1:
            home_attr = self.get_single_attribute(home_entries, 'automountInformation')
            if  re.search(r'(\S+:/?/.*)', home_attr):
                home_dir = re.search(r'(\S+:/?/.*)', home_attr).group(1)
                setattr(entry, 'automountHome', home_dir)
        return entry


    def print_csv(self, entries):
        csv_str = "\n"
        for entry in entries:
            person_cn = entry.cn
            expire_days = self.get_account_expiration(entry)
            first, last = self.filter_name_parts(person_cn)
            csv_str += "{},".format(first)
            csv_str += "{},".format(last)
            csv_str += "{},".format(entry.accountEndDate)
            csv_str += "{},".format(expire_days)
            csv_str += "{},".format(entry.uid)
            csv_str += "{},".format(entry.mail)
            csv_str += "{},".format(entry.telephoneNumber)
            csv_str = re.sub(r',\s*$', "", csv_str)
            csv_str += "\n"
        return csv_str


    def create_random_password_hash(self):
        low = 'abcdefghjkmnpqrstuvwxyz'
        up = 'ABCDEFGHJKMNPQRSTUVWXYZ'
        num = '23456789';
        new_pass = "{}{}{}{}{}{}@{}".format(random.choice(low), random.choice(num), random.choice(up), random.choice(num), random.choice(num), random.choice(up), random.choice(up))
        salt = os.urandom(4)
        hashed = hashlib.sha1(new_pass)
        hashed.update(salt)
        salted = "{SSHA}" + encode(hashed.digest() + salt)[:-1]
        return new_pass, salted


    def create_ldap_password_hash(self, password):
        new_pass = password[:]
        salt = os.urandom(4)
        hashed = hashlib.sha1(new_pass)
        hashed.update(salt)
        salted = "{SSHA}" + encode(hashed.digest() + salt)[:-1]
        return new_pass, salted
    
    
    def get_create_account_attachments(self, home_dir):
        docs = []
        new_user = "{}/PDF.pdf".format(self.new_user_doc_dir)
        if re.search(r'(home_lim)', home_dir) is None:
            docs.append(pbs_training)
        docs.append(new_user)
        docs.append(token_setup)
        return docs

    
    def build_email_for_account_archive(self, conn, person_entry, home_dir, cc, to, group_list, admin=getpass.getuser(), skip_user=False):
        rmail_obj = robo_mail.RoboMail()
        cn = person_entry.cn
        uid = person_entry.uid
        #group_list = self.get_users_groups(conn, uid)
        #print(group_list)
        subject = "account archival for {}".format(cn)
        admin_email, to_list, cc_list, first, last, sponsor = self.build_admin_email(conn, person_entry, home_dir, cc, to, rmail_obj, 'sponsor', skip=skip_user)
        body = self.create_archive_email_body(sponsor, cn, group_list)
        signature = rmail_obj.create_email_signature(admin)
        body += "\n{}\n".format(signature)
        attachment_list = ["{}/PDF.pdf".format(self.new_user_doc_dir)]
        rmail_obj.send_mail(admin_email, to_list, cc_list, subject, body, pdf_list=attachment_list)
        return sponsor


    def build_email_for_account_creation(self, conn, person_entry, home_dir, cc, to, admin=getpass.getuser()):
        rmail_obj = robo_mail.RoboMail()
        uid = person_entry.uid
        subject = "Account"
        admin_email, to_list, cc_list, first, last, sponsor = self.build_admin_email(conn, person_entry, home_dir, cc, to, rmail_obj, 'user')
        body = self.create_email_body(home_dir, first, uid)
        signature = rmail_obj.create_email_signature(admin)
        body += "\n{}\n".format(signature)
        attachment_list = self.get_create_account_attachments(home_dir)
        rmail_obj.send_mail(admin_email, to_list, cc_list, subject, body, pdf_list=attachment_list)
        return sponsor


    def build_email_for_account_disable(self, conn, person_entry, cc, to, admin=getpass.getuser()):
        rmail_obj = robo_mail.RoboMail()
        uid = person_entry.uid
        admin_email, to_list, cc_list, first, last, sponsor = self.build_admin_email(conn, person_entry, None, cc, to, rmail_obj, 'sponsor')
        subject = "account temporarily disabled for {} {}".format(first, last)
        body = self.create_disable_email_body(sponsor, "{} {}".format(first, last))
        signature = rmail_obj.create_email_signature(admin)
        body += "\n{}\n".format(signature)
        attachment_list = []
        rmail_obj.send_mail(admin_email, to_list, cc_list, subject, body, pdf_list=attachment_list)
        return sponsor


    def build_admin_email(self, conn, person_entry, home_dir, added_cc_list, added_to_list, rmail_obj, who_to, admin=getpass.getuser(), skip=False):
        #print(who_to)
        uid = person_entry.uid
        full_name = person_entry.cn
        new_user_email = person_entry.mail
        first, last = self.filter_name_parts(full_name)
        ###############################################

        ### SPONSOR ######################################################
        sponsor_entries = self.get_sponsor_entry(conn, sponsor_name)
        sponsor_email = self.get_single_attribute(sponsor_entries, 'mail')
        sponsor_email = re.sub(r"'", "" , sponsor_email)
        sponsor_email = re.sub(r'"', "" , sponsor_email)
        ##################################################################

        ### Sender ######################################################
        #rmail_obj = robo_mail.RoboMail()
        check = rmail_obj.is_person_in_db(admin)
        if check == 0:
            admin = rmail_obj.get_username_for_reply_mail()
        admin_email = rmail_obj.people['person'][admin]['attr']['email']
        #################################################################
        
        cc_list=[]
        to_list=[]
        ### Email ######################################################
        if re.search(r'user', who_to, re.I) is not None:
            to_list = [new_user_email]
            to_list.extend(added_to_list)
            cc_list = rmail_obj.get_cc_list()
            cc_list.extend(added_cc_list)
            if sponsor_email: cc_list.append(sponsor_email)
        elif re.search(r'sponsor', who_to, re.I) is not None:
            to_list = [sponsor_email]
            to_list.extend(added_to_list)
            cc_list = rmail_obj.get_cc_list()
            cc_list.extend(added_cc_list)
            if not skip: cc_list.append(new_user_email)
        uniq_cc = list(set(cc_list))
        ###############################################################
        return admin_email, to_list, uniq_cc, first, last, sponsor_name


    def compare_ldap_structures(self, master_name, master_dict, secondary_name, secondary_dict):
        for key in master_dict:
            if not key in secondary_dict:
                print("Key {} was found in {} but seems to be missing from {}".format(key, master_name, secondary_name))
                return 0
            for key2 in master_dict[key]:
                if key2 == 'pwdFailureTime': continue
                #if key2 == 'pwdAccountLockedTime': continue
                if not key2 in secondary_dict[key]:
                    print("Key {} {} was found in {} but seems to be missing from {}".format(key, key2, master_name, secondary_name))
                    return 0
                m_list = list(master_dict[key][key2])
                s_list = list(secondary_dict[key][key2])
                m_list.sort()
                s_list.sort()
                cnt = 0
                for val in m_list:
                    val2 = s_list[cnt]
                    if val != val2:
                        print("DN: {} {} Attribute {} was found in {} but seems to be missing from {}".format(key, key2, val, master_name, secondary_name))
                        return 0
                    cnt+=1
        return 1


    def get_manager_uid_from_ldap(self, entry):
        if hasattr(entry, 'manager'):
            manager_full = entry.manager
            if re.search(r',cn=\S+', manager_full) is not None:
                manager_uid = re.search(r',cn=(\S+)', manager_full).groups(1)
                return manager_uid
        return False
        

    def get_sp_dict_attr(self, sp_dict, attr):
        val = ""
        if attr in sp_dict:
            val = sp_dict[attr]
            return val
        return val




    def check_ldap_attr_for_trailing_space(self, entry, QA_dict):
        uid = entry.uid
        check_description = "Check attributes for trailing spaces"
        check_id = "qa_trailing_spaces"
        QA_dict['checks']['users'][uid][check_id] = {}
        QA_dict['checks']['users'][uid][check_id]['desc'] = check_description
        found_space_flag = 0
        found_list = []
        for ldap_attr, ldap_val in entry.__dict__.iteritems():
            if isinstance(ldap_val, list):
                for item in ldap_val:
                    if re.search(r'\s+$', item) is not None:
                        found_space_flag = 1
                        found_list.append(item)
            else:
                if re.search(r'\s+$', ldap_val) is not None:
                    found_space_flag = 1
                    found_list.append(ldap_attr)
        if found_space_flag == 0:
            QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'PASS'
        else:
            QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'FAIL'
            QA_dict['checks']['users'][uid][check_id]['error'] = "The following fields had values which contained trailing white space {}".format(found_list)

            
    def check_ldap_for_end_date(self, entry, QA_dict):
        uid = entry.uid
        check_description = "Check LDAP account for end date"
        check_id = "qa_end_date"
        QA_dict['checks']['users'][uid][check_id] = {}
        QA_dict['checks']['users'][uid][check_id]['desc'] = check_description
        if hasattr(entry, 'accountEndDate'):
            QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'PASS'
        else:
            QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'FAIL'


    def check_ldap_for_creation_date(self, entry, QA_dict):
        uid = entry.uid
        check_description = "Check LDAP account for creation date"
        check_id = "qa_creation_date"
        QA_dict['checks']['users'][uid][check_id] = {}
        QA_dict['checks']['users'][uid][check_id]['desc'] = check_description
        if hasattr(entry, 'createTimestamp'):
            QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'PASS'
        else:
            QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'FAIL'


    def check_ldap_for_user_password(self, entry, QA_dict):
        uid = entry.uid
        check_description = "Check LDAP account for user password"
        check_id = "sec_user_password"
        QA_dict['checks']['users'][uid][check_id] = {}
        QA_dict['checks']['users'][uid][check_id]['desc'] = check_description
        if hasattr(entry, 'userPassword'):
            QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'PASS'
        else:
            QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'FAIL'


    def check_password_encryption_strength(self, entry, QA_dict):
        uid = entry.uid
        encryption_type = 'ssha'
        check_description = "Check for strong encryption on password"
        check_id = "sec_encrypt_type"
        QA_dict['checks']['users'][uid][check_id] = {}
        QA_dict['checks']['users'][uid][check_id]['desc'] = check_description
        password_hash = entry.userPassword
        ptype = re.match(r'{(.*?)}', password_hash).group(1)
        ptype_lc = ptype.lower()
        if ptype_lc != encryption_type:
            QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'FAIL'
            QA_dict['checks']['users'][uid][check_id]['error'] = "Looking for password hash type {} but found {}".format(encryption_type, ptype_lc)
        else:
            QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'PASS'


    def check_password_not_more_than_6_months(self, entry, QA_dict, conn):
        uid = entry.uid
        six_months_ago = datetime.date.today() - relativedelta(months=+6)
        check_description = "Password has changed within 6 months"
        check_id = "sec_password_age"
        QA_dict['checks']['users'][uid][check_id] = {}
        QA_dict['checks']['users'][uid][check_id]['desc'] = check_description
        if hasattr(entry, 'pwdChangedTime'):
            passwd_change_time = entry.pwdChangedTime
            pyear, pmonth, pday = re.search(r'(\d{4})(\d{2})(\d{2})', passwd_change_time).group(1, 2, 3)
            pdate = "{}-{}-{}".format(pyear, pmonth, pday)
            last_passwd_change_date = self.parse_date_for_datetime(pdate)
            if last_passwd_change_date < six_months_ago:
                QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'FAIL'
                QA_dict['checks']['users'][uid][check_id]['error'] = "Password is more than 6 months old {}".format(passwd_change_time)
                self.disable_account_with_password_more_than_expired(conn, entry)
            else:
                QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'PASS'
        else:
            QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'FAIL'
            QA_dict['checks']['users'][uid][check_id]['error'] = "No attribute 'pwdChangedTime'"


    def disable_account_with_password_more_than_expired(self, conn, entry):
        uid = entry.uid
        user_dn = entry.dn
        ### Add 3 weeks slop for running jobs
        six_months_ago = datetime.date.today() - relativedelta(months=+6, weeks=+3)
        #six_months_ago = datetime.date.today() - relativedelta(months=+12, weeks=+3)
        if hasattr(entry, 'pwdChangedTime'):
            passwd_change_time = entry.pwdChangedTime
            pyear, pmonth, pday = re.search(r'(\d{4})(\d{2})(\d{2})', passwd_change_time).group(1, 2, 3)
            pdate = "{}-{}-{}".format(pyear, pmonth, pday)
            last_passwd_change_date = self.parse_date_for_datetime(pdate)
            if last_passwd_change_date < six_months_ago:
                #print("Found one {}".format(uid))
                #print("{}".format(uid))
                #print(last_passwd_change_date)
                if hasattr(entry, 'shadowExpire'):
                    self.modify_ldap_attribute(conn, user_dn, entry, 'shadowExpire', '0', uid)
                else:
                    self.add_ldap_attribute(conn, user_dn, 'shadowExpire', '0', uid)



    def check_for_unexpected_fields(self, entry, QA_dict):
        uid = entry.uid
        check_description = "Check for unexpected fields"
        check_id_base = "qa_unexpected_fields"
        found_obs_flag = 0
        fields = {
            "accountEndDate", "automountHome", "automountScratch", "cn", "createTimestamp", "creatorsName", "daysUntilExpire",
            "departmentNumber", "dn", "employeeNumber", "employeeType", "entryCSN", "entryDN", "entryUUID", "gecos", "gidNumber",
            "givenName", "hasSubordinates", "homeDirectory", "loginShell", "mail", "manager", "mobile",
            "modifiersName", "modifyTimestamp", "objectClass", "pwdChangedTime", "pwdHistory", "shadowLastChange", "shadowMax", "sn",
            "structuralObjectClass", "subschemaSubentry", "telephoneNumber", "uid", "uidNumber", "userPassword",
            "securityPlanNumber", "pwdFailureTime"
        }
        for ldap_attr, ldap_val in entry.__dict__.iteritems():
            if not ldap_attr in fields:
                found_obs_flag = 1
                check_id = "{}_{}".format(check_id_base,ldap_attr)
                QA_dict['checks']['users'][uid][check_id] = {}
                QA_dict['checks']['users'][uid][check_id]['desc'] = check_description
                QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'FAIL'
                QA_dict['checks']['users'][uid][check_id]['error'] = "Unexpected field {} found".format(ldap_attr)
        if found_obs_flag == 0:
            QA_dict['checks']['users'][uid][check_id_base] = {}
            QA_dict['checks']['users'][uid][check_id_base]['pass_fail'] = 'PASS'
            QA_dict['checks']['users'][uid][check_id_base]['desc'] = check_description
            

    def check_uid_matches_dn(self, entry, QA_dict):
        uid = entry.uid
        check_description = "uid matches name in dn"
        check_id = "qa_uid_matches_dn"
        QA_dict['checks']['users'][uid][check_id] = {}
        QA_dict['checks']['users'][uid][check_id]['desc'] = check_description
        dn = entry.dn
        dn_user = re.search(r'uid=([^,]+)', dn, re.I).group(1)
        if dn_user.lower() != uid.lower():
            QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'FAIL'
            QA_dict['checks']['users'][uid][check_id]['error'] = "dn user name did not match uid".format(dn_user.lower(), uid.lower())
        else:
            QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'PASS'



    def check_uid_matches_gid(self, entry, QA_dict):
        uid = entry.uid
        uidn = entry.uidNumber
        gidn = entry.gidNumber
        check_description = "Gid matches uid"
        check_id = "qa_gid_is_uid"
        QA_dict['checks']['users'][uid][check_id] = {}
        QA_dict['checks']['users'][uid][check_id]['desc'] = check_description
        if uidn == gidn:
           QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'PASS'
        else:
           QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'FAIL'
           QA_dict['checks']['users'][uid][check_id]['error'] = "gid is {} but uid is {}".format(gidn, uidn)


    def check_pwdChangedTime_matches_shadowLastChange(self, entry, QA_dict):
        uid = entry.uid
        uidn = entry.uidNumber
        gidn = entry.gidNumber
        check_description = "pwdChangedTime_matches_shadowLastChange"
        check_id = "qa_gid_pwdCT_is_shadowLC"
        QA_dict['checks']['users'][uid][check_id] = {}
        QA_dict['checks']['users'][uid][check_id]['desc'] = check_description
        ldap_slc = ""
        if hasattr(entry, 'shadowLastChange'):
            ldap_slc = entry.shadowLastChange
        else:
            ldap_slc = 'NEVER'
        days, epoch_passwd_chage_time = self.get_days_from_password_change(entry)
        if str(epoch_passwd_chage_time) != str(ldap_slc):
           QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'FAIL'
           QA_dict['checks']['users'][uid][check_id]['error'] = "pwdChangedTime is {} but shadowLastChange is {}".format(ldap_slc, epoch_passwd_chage_time)
        else:
            QA_dict['checks']['users'][uid][check_id]['pass_fail'] = 'PASS'



    def find_users_with_failed_QA(self, QA_dict):
      continue_user = Continue1()          
      for user in sorted(QA_dict['checks']['users'].keys()):
        try:
            for check in sorted(QA_dict['checks']['users'][user].keys()):
                #print(check)
                pass_fail = QA_dict['checks']['users'][user][check]['pass_fail']
                if re.search(r'fail', pass_fail, re.I) is not None:
                    self.QA_report(QA_dict['checks']['users'][user], user)
                    raise continue_user
        except Continue1:
            continue


    def QA_report(self, QA_dict, user):
        print('#' * 150)
        print("###                                     {}").format(user)
        print('#' * 150)
        for check in sorted(QA_dict.keys()):
            pass_fail = QA_dict[check]['pass_fail']
            description = QA_dict[check]['desc']
            if pass_fail == 'FAIL':
                print("{0:<42} {1:<8} {2:<40}".format(check, pass_fail, description)),
            if 'error' in  QA_dict[check]:
                print(" {}".format(QA_dict[check]['error'])),
            if pass_fail == 'FAIL': print("")
        print("\n")


    def export_importable_ldif(self, dn, dict_entry, export_path):
        if not isinstance(dict_entry, dict):
            print("Need to export ldif from a dictionary. Please use _get_query for your search")
            sys.exit()
        new_dict = dict_entry.copy()
        new_dict.pop("createTimestamp", None)
        new_dict.pop("pwdChangedTime", None)
        new_dict.pop("entryCSN", None)
        new_dict.pop("modifyTimestamp", None)
        new_dict.pop("entryDN", None)
        new_dict.pop("subschemaSubentry", None)
        new_dict.pop("modifiersName", None)
        new_dict.pop("creatorsName", None)
        new_dict.pop("hasSubordinates", None)
        new_dict.pop("pwdHistory", None)
        new_dict.pop("pwdFailureTime", None)
        new_dict.pop("structuralObjectClass", None)
        new_dict.pop("entryUUID", None)
        if re.search(r'People', dn) is not None:
            new_dict['shadowExpire'] = ['0']
            new_dict['pwdReset'] = ['TRUE']
            new_dict['userPassword'] = ['PASSHASHGOESHERE']

        if os.path.isfile(export_path):
            date = time.strftime('%Y-%m-%d-%H:%M:%S').rstrip()
            os.rename(export_path, "{}.{}".format(export_path, date))
        
        writer = ldif.LDIFWriter(open(export_path, 'wb'))
        writer.unparse(dn, new_dict)


    def export_full_ldif_sans_pass(self, dn, dict_entry, export_path):
        if not isinstance(dict_entry, dict):
            print("Need to export ldif from a dictionary. Please use _get_query for your search")
            sys.exit()
        new_dict = dict_entry.copy()
        if re.search(r'People', dn) is not None:
            new_dict['userPassword'] = ['PASSHASHGOESHERE']
            new_dict.pop("pwdHistory", None)

        if os.path.isfile(export_path):
            date = time.strftime('%Y-%m-%d-%H:%M:%S').rstrip()
            os.rename(export_path, "{}.{}".format(export_path, date))

        writer = ldif.LDIFWriter(open(export_path, 'wb'))
        writer.unparse(dn, new_dict)


    def archive_ldif_before_delete(self, conn, userid, dn, filters, archive_label, ldif_dir, searchScope=ldap.SCOPE_SUBTREE, attributes=["+","*"]):
        entries = self._get_query(conn, filters, dn, searchScope, attributes)
        if len(entries) != 1:
            print("Did not find exactly 1 entry for {}\n{}".format(dn, entries))
            sys.exit()
        for one_dn in entries:
            try:
                self.export_importable_ldif(one_dn, entries[one_dn], '{}/{}_{}_importable.ldif'.format(ldif_dir, userid, archive_label))
                self.export_full_ldif_sans_pass(dn, entries[one_dn], '{}/{}_{}_full.ldif'.format(ldif_dir, userid, archive_label))
            except:
                print(sys.exc_info()[0])
        entries = self.__get_query(conn, filters, dn, searchScope, attributes)
        try:
            self.check_for_more_than_one_entry(entries)
            user_entry_obj = entries[0]
            self.delete_ldap_entry(conn, one_dn, userid)
        except:
            print(sys.exc_info()[0])


    def archive_users_groups(self, conn, userid, dest_homedir, export_dir):
        group_list = self.get_users_groups(conn, userid)
        group_export_path = "{}/{}_ldap_groups.txt".format(export_dir, userid)

        if os.path.isfile(group_export_path):
            date = time.strftime('%Y-%m-%d-%H:%M:%S').rstrip()
            os.rename(group_export_path, "{}.{}".format(group_export_path, date))
        with open(group_export_path, "w") as group_fh:
            for group in group_list:
                group_fh.write("{}\n".format(group))
        for group in group_list:
            group_entries = self.group_search(conn, group, exact=1)
            if len(group_entries) !=1 :
                sys.exit("\n\nCould not find exactly one group with the name of {}!\n".format(group))
            group_entry_obj = group_entries[0]
            dn = group_entry_obj.dn
            self.remove_from_ldap_list(conn, dn, userid, userid)
        return group_list
            

    def get_home_dir_from_automount(self, conn, userid):
        dn = "automountKey={},automountMapName=auto.home,dc=your,dc=domain,dc=com".format(userid)
        filters = "(automountKey={})".format(userid)
        entries = self.__get_query(conn, filters, dn)
        self.check_for_more_than_one_entry(entries)
        user_entry_obj = entries[0]
        automount = user_entry_obj.automountInformation
        home_dir = re.search(r'/(home_.*?)/', automount).group(1)
        return home_dir


    def check_wrong_AD_uid(self, uid):
        new_uid = uid[:]
        white_list = self.ldap_to_AD_whitelist()
        
        for person in white_list['people']:
            if 'ad_name' in white_list['people'][person]:
                ad_name = white_list['people'][person]['ad_name']
                if uid == ad_name:
                    new_uid = person
        return new_uid


    def ldif_to_ldap_obj(self, ldif_path, ):
        reader = ldif.LDIFRecordList(open(ldif_path, "rb"))
        reader.parse()
        dn, ldif_dict = reader.all_records[0]
        entry_struct = [[]]
        entry_struct[0] = (dn, ldif_dict)
        entry = LdapResults(entry_struct)
        return entry


    def add_ldif_to_ldap(self, conn, ldif_path, userid):
        reader = ldif.LDIFRecordList(open(ldif_path, "rb"))
        reader.parse()
        dn, entry = reader.all_records[0]
        ldif_content = ldap.modlist.addModlist(entry)
        self.add_ldap_entry(conn, dn, ldif_content, userid)


    def sync_pwdChangedTime_2_shadowLastChange(self, conn, entry):
        user_dn = entry.dn
        user_cn = entry.cn
        uid = entry.uid
        ldap_slc = ''
        if hasattr(entry, 'shadowLastChange'):
            ldap_slc = entry.shadowLastChange
        else:
            ldap_slc = 'NEVER'
        days, epoch_passwd_chage_time = self.get_days_from_password_change(entry)
        if str(epoch_passwd_chage_time) != str(ldap_slc):
            if hasattr(entry, 'shadowLastChange'):
                self.modify_ldap_attribute(conn, user_dn, entry, 'shadowLastChange', str(epoch_passwd_chage_time), uid)
            else:
                self.add_ldap_attribute(conn, user_dn, 'shadowLastChange', str(epoch_passwd_chage_time), uid)
        

class LdapResults:
    
    def __init__(self, result_data, **kwargs):
        dn = result_data[0][0]
        setattr(self, 'dn', dn)
        for attribute in result_data[0][1]:
            if len(result_data[0][1][attribute]) == 1:
                setattr(self, attribute, result_data[0][1][attribute][0])
            else:
                setattr(self, attribute, result_data[0][1][attribute])


    def get_val(self, attribute):
        return self.attribute        


    def print_entry(self):
        print('#' * 70)
        print("###  DN: {}").format(self.dn)
        print('#' * 70)
        for attribute in sorted(vars(self)):
            print("{0:<25}").format(attribute),
            if isinstance(attribute, list):
                for val in attribue:
                    print("{}").format(val),
            else:
                if attribute == 'pwdAccountLockedTime':
                    print("{} LOCKED").format(getattr(self, attribute))
                else:
                    print(getattr(self, attribute))
                

    def print_group_entry(self, ldap_obj, conn):
        mydn = self.dn[:]
        mydn = re.sub(r'cn=|,.*', '', mydn)
        print("\nGROUP: {0:<20}\n".format(mydn))
        user_list = []
        if hasattr(self, 'memberUid'):
            if isinstance(self.memberUid, list):
                for member in self.memberUid:
                    user_list.append(member)
            else:
                user_list.append(self.memberUid)
        for userid in user_list:
            #print(userid)
            entries = ldap_obj.uid_search(conn, userid, exact=1)
            #print(entries)
            if len(entries) != 1: continue
            ldap_obj.check_for_more_than_one_entry(entries)
            user_entry_obj = entries[0]
            user_entry_obj.ci_print()


    def ci_print(self):
        print('USERNAME: {0:<40} UID: {1:<10} EMAIL: {2}'.format(self.cn, self.uid, self.mail))




class LdifFileParser(ldif.LDIFParser):

    def __init__(self, input_file):
        myfile = open(input_file, "rb")
        ldif.LDIFParser.__init__(self, myfile)
