#	Copyright 2018 Battelle Energy Alliance, LLC

import os
import sys
import re
import json
import subprocess
import glob
import hashlib
import socket
import time
from subprocess import call
import getpass

class FileWatch(object):
    
    def __init__(self):
        self.base_dir = '/file/to/FileWatch'

    ### Check file to see if its in the db and if the md5s match ##########################
    def check_file_db(self, monitored_file, file_dict, hostname, update=0):
        existing_file = 1
        if os.path.isfile(monitored_file):
            current_md5_sum = hashlib.md5(open(monitored_file, 'rb').read()).hexdigest()
            if monitored_file in file_dict:
                old_md5_sum = file_dict[monitored_file]
                if current_md5_sum == old_md5_sum:
                    pass
                    #print("MD5s match for {}".format(monitored_file))
                else:
                    if update:
                        file_dict[monitored_file] = current_md5_sum
                    else:
                        print("ERROR: MD5s did not match for {}".format(monitored_file))
            else:
                print("Adding new file: {}".format(monitored_file))
                file_dict[monitored_file] = current_md5_sum
                existing_file = 0
        else:
            print("ERROR: {} is not a file".format(monitored_file))
        return file_dict, existing_file
    #########################################################################################


    def backup_file_db(self, file_db_path):
        now = time.strftime('%Y-%m-%d-%H-%M-%S').rstrip()
        if os.path.isfile(file_db_path):
            os.rename(file_db_path, "{}.{}".format(file_db_path, now))


    def get_hostname(self):
        hostname = socket.gethostname()
        hostname = re.sub(r'\..*', '', hostname)
        return hostname
    

    def get_base_config_file(self):
        base_dir = self.base_dir
        conf_path = "{}/conf/base_file_watch.conf".format(base_dir)
        return conf_path


    def get_host_config_file(self, hostname=get_hostname('FileWatch')):
        base_dir = self.base_dir
        host_dir = "{}/conf/{}".format(base_dir,hostname)
        if not os.path.exists(host_dir): os.makedirs(host_dir)
        conf_path = "{}/{}_file_watch.conf".format(host_dir,hostname)
        if not os.path.isfile(conf_path):
            print("Could not find a file watch configuration file for {}: only using the base file".format(hostname))
        return conf_path


    def get_host_db_file(self, hostname=get_hostname('FileWatch')):
        base_dir = self.base_dir
        host_dir = "{}/db/{}".format(base_dir,hostname)
        if not os.path.exists(host_dir): os.makedirs(host_dir)
        db_path = "{}/{}_file_db.json".format(host_dir,hostname)
        return db_path


    def get_host_changelog_file(self, hostname=get_hostname('FileWatch')):
        base_dir = self.base_dir
        host_dir = "{}/changelog/{}".format(base_dir,hostname)
        if not os.path.exists(host_dir): os.makedirs(host_dir)
        cl_path = "{}/{}_changelog.md".format(host_dir,hostname)
        return cl_path


    def get_file_list_from_conf(self, conf_path):
        files = []
        excludes = []
        if os.path.isfile(conf_path):
            with open(conf_path) as conf_fh:
                for line in iter(conf_fh):
                    line = line.rstrip()
                    if re.search(r'^\s*$', line) is not None: continue
                    if re.search(r'^\s*#', line) is not None: continue
                    if re.search(r'\s*exclude\s+\S+', line, re.I) is not None:
                        files_to_ex = re.search(r'\s*exclude\s+(\S+)', line, re.I).group(1)
                        temp_ex = glob.glob(files_to_ex)
                        if not temp_ex:
                            excludes.append(files_to_ex)
                        for one_file in temp_ex:
                            excludes.append(one_file)
                    else:
                        temp_files = glob.glob(line)
                        if not temp_files:
                            files.append(line)
                        for one_file in temp_files:
                            files.append(one_file)
        return files, excludes


    def remove_excludes(self, files, excludes):
        new_files = []
        all_excludes = []
        for exclude in excludes:
            temp_files = glob.glob(exclude)
            for temp_file in temp_files:
                all_excludes.append(temp_file)
        for include in files:
            if include not in all_excludes:
                new_files.append(include)
        return new_files
                

    def check_hosts_file_changes(self, hostname=get_hostname('FileWatch')):
        new_db = 0
        no_files_added = 1
        db_path = self.get_host_db_file(hostname)
        file_dict = self.get_file_watch_db(db_path)
        if not os.path.isfile(db_path):
            new_db = 1
        file_list = self.get_final_file_list(hostname)
        for one_file in file_list:
            if os.path.isfile(one_file):
                file_dict, new_file_check = self.check_file_db(one_file, file_dict, hostname)
                no_files_added &= new_file_check
            elif not os.path.isfile(one_file) and one_file in file_dict:
                print("ERROR: {} is in database but file is no longer there".format(one_file))
        if new_db or not no_files_added:
            self.backup_file_db(db_path)
            self.write_new_file_db(db_path, file_dict)


    def get_final_file_list(self, hostname):
        all_files = []
        all_excludes = []
        base_conf_path = self.get_base_config_file()
        base_files, base_excludes = self.get_file_list_from_conf(base_conf_path)
        host_conf_path = self.get_host_config_file(hostname)
        host_files, host_excludes = self.get_file_list_from_conf(host_conf_path)
        for base_file in base_files:
            all_files.append(base_file)
        for host_file in host_files:
            all_files.append(host_file)
        for base_ex in base_excludes:
            all_excludes.append(base_ex)
        for host_ex in host_excludes:
            all_excludes.append(host_ex)
        new_list =  self.remove_excludes(all_files, all_excludes)
        return new_list


    def write_new_file_db(self, db_path, file_dict):
        db_fh = open(db_path, 'w')
        json.dump(file_dict, db_fh, sort_keys=True, indent=2)
        db_fh.close()


    def get_file_watch_db(self, db_path):
        file_dict = {}
        if os.path.isfile(db_path):
            file_dict = json.load(open(db_path))
        return file_dict        


    def check_in_files(self, file_list, hostname):
        file_db_path = self.get_host_db_file(hostname)
        file_dict = self.get_file_watch_db(file_db_path)
        for one_file in file_list:
            if os.path.isfile(one_file):
                md5_sum = hashlib.md5(open(one_file, 'rb').read()).hexdigest()
                if one_file in file_dict:
                    print("Updating hash for {}".format(one_file))
                else:
                    print("{} exists but is not in the database adding it .... Put it in the conf file if you want to track it permanently".format(one_file))
                file_dict[one_file] = md5_sum
            else:
                print("ERROR: File --{}-- Could not be found ... Not adding it to the database".format(one_file))
        self.backup_file_db(file_db_path)
        self.write_new_file_db(file_db_path, file_dict)


    def update_change_log(self, file_list, hostname):
        self.check_in_files(file_list, hostname)
        new_file = 0
        changelog_path = self.get_host_changelog_file(hostname)
        change_log = ""
        if not os.path.isfile(changelog_path):
            change_log += self.get_header()
            new_file = 1
        else:
            header_check = self.check_for_header(changelog_path)
            if not header_check:
                change_log += self.get_header()
        change_log += self.get_changelog_template(file_list)
        self.insert_changelog_text(changelog_path, change_log, new_file)
        EDITOR = os.environ.get('EDITOR','vim')
        call([EDITOR, changelog_path])


    def insert_changelog_text(self, changelog_path, text, new_file=0):
        new_content = ""
        if not new_file:
            content = ""
            with open(changelog_path, 'r') as cl_fh:
                content = cl_fh.read()
            new_content = re.sub(r'(PLEASE DO NOT MAKE CHANGES ABOVE THIS LINE.*?)\n', r'\1\n{}'.format(text), content)
        else:
            new_content = text
        with open(changelog_path, 'w') as cl_fh:
                cl_fh.write(new_content)


    def check_for_header(self, changelog_path):
        content = ""
        with open(changelog_path, 'r') as cl_fh:
            content = cl_fh.read()
        if re.search(r'PLEASE DO NOT MAKE CHANGES ABOVE THIS LINE', content) is not None:
            return 1
        else:
            return 0
           

    def file_list_to_md(self, file_list):
        md_text = ""
        for one_file in file_list:
            md_text += "- {}\n".format(one_file)
        return md_text


    def does_server_exist(self, hostname):
        try:
            output = subprocess.check_output("ping -c 1 {}".format(hostname), shell=True)
        except Exception, e:
            print('Server "{}" could not be found'.format(hostname))
            sys.exit()
        return 1   


    def get_changelog_template(self, file_list):
        date = time.strftime('%Y-%m-%d').rstrip()
        owner = getpass.getuser()
        file_text = self.file_list_to_md(file_list)
        template = """
## [Major.Minor.Patch] - {} - {}
### Added
- 
- 

### Changed
{}
- 
- 

### Removed
- 
- 

### Fixed
- 
- 


""".format(date, owner, file_text)
        return template 


    def get_header(self):
        header = """# Changelog
Changes to any file that is tracked on the system should be documented in this file

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

PLEASE DO NOT MAKE CHANGES ABOVE THIS LINE


"""
        return header


