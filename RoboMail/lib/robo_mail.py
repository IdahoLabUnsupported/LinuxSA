import json
import re
import sys
import getpass
import smtplib
import email
import mimetypes
import email.mime.application
from email.MIMEText import MIMEText

#	Copyright 2018 Battelle Energy Alliance, LLC

class RoboMail(object):
    
    def __init__(self, **test):
        self.__people_dict = '/path/to/people.py'
        people = {}
        with open(self.__people_dict) as data_file:
            people = json.load(data_file)
        setattr(self, 'people', people)


    def create_email_signature(self, user_name):
        fn = self.people['person'][user_name]['attr']['first_name']
        ln = self.people['person'][user_name]['attr']['last_name']
        title = self.people['person'][user_name]['attr']['title']
        affiliation = self.people['person'][user_name]['attr']['affiliation']
        email = self.people['person'][user_name]['attr']['email']
        desk_phone = self.people['person'][user_name]['attr']['desk_phone']
        cell_phone = self.people['person'][user_name]['attr']['cell_phone']
        template = ""
        if re.search(r'USERNAME', user_name) is not None:
            template = "Thanks,\n\n{} {}\n{}\nEmail: {}\nDesk: {}\nCell: {}\n".format(fn, ln, title, email, desk_phone, cell_phone)
        else:
            template = "Thanks,\n\n{} {} ----- {}\n{}\nDesk: {}     Mobile: {}\n".format(fn, ln, affiliation, title, desk_phone, cell_phone)
        return template


    def is_person_in_db(self, person):
            if person in self.people['person']:
                return 1
            else:
                return 0


    def get_username_for_reply_mail(self):
        print("Could not figure out which admin you are (maybe you are root?)")
        persons = self.people['person'].keys()
        response = raw_input("Please input one of the following usernames for a email signature {}: ".format(json.dumps(persons)))
        if not any(response in s for s in persons):
            print("\n\n{} was not in admin database\n").format(response)
            sys.exit(0)
        return response
            

    def get_cc_list(self):
        sender = getpass.getuser()
        static_cc_list = ('USER1', 'USER2')
        new_cc_list = []
        for cc in static_cc_list:
            if cc != sender:
                new_cc_list.append(self.people['person'][cc]['attr']['email'].lower())
        if not sender in self.people['person']:
            new_cc_list.append(self.people['person']['myerds']['attr']['email'].lower())
        else:
            new_cc_list.append(self.people['person'][sender]['attr']['email'].lower())
        return new_cc_list


    def send_mail(self, from_mail, to_list, cc_list, subject_str, body_str, pdf_list=None):
        if pdf_list is None: pdf_list = []
        merged_list = list(set(to_list + cc_list))
        print("\n\n\n")
        print("FROM: {}").format(from_mail)
        print("TO: {}").format(to_list)
        print("CC: {}").format(cc_list)
        print("SUBJECT: {}").format(subject_str)
        #print("Merged: {}").format(merged_list)
        if pdf_list is not None: print("ATTACHMENTS: {}").format(pdf_list)
        print("{}\n\n\n").format(body_str)
        
        email_response = raw_input("If you would like to email the previous text, please type (y/Y):\n")
        if re.search(r'^y$|^Y$|^yes$', email_response) is not None:
            COMMASPACE = ', '
            msg = email.mime.Multipart.MIMEMultipart()
            msg['TO'] = COMMASPACE.join(to_list)
            msg['CC'] = COMMASPACE.join(cc_list)
            msg['FROM'] = from_mail
            msg['SUBJECT'] = subject_str
            for pdf in pdf_list:
                fp=open(pdf,'rb')
                att = email.mime.application.MIMEApplication(fp.read(),_subtype="pdf")
                fp.close()
                att.add_header('Content-Disposition','attachment',filename=pdf)
                msg.attach(att)
            msg.attach(MIMEText(body_str, 'plain'))
            
            s = smtplib.SMTP('MAILHOST')
            s.starttls()
            s.sendmail(from_mail, merged_list, msg.as_string())
            s.quit()
       
    def send_mail_non_interactive(self, from_mail, to_list, cc_list, subject_str, body_str, pdf_list=None):
        if pdf_list is None: pdf_list = []
        merged_list = list(set(to_list + cc_list))
        print("\n\n\n")
        print("FROM: {}").format(from_mail)
        print("TO: {}").format(to_list)
        print("CC: {}").format(cc_list)
        print("SUBJECT: {}").format(subject_str)
        #print("Merged: {}").format(merged_list)
        if pdf_list is not None: print("ATTACHMENTS: {}").format(pdf_list)
        print("{}\n\n\n").format(body_str)
        
        COMMASPACE = ', '
        msg = email.mime.Multipart.MIMEMultipart()
        msg['TO'] = COMMASPACE.join(to_list)
        msg['CC'] = COMMASPACE.join(cc_list)
        msg['FROM'] = from_mail
        msg['SUBJECT'] = subject_str
        for pdf in pdf_list:
            fp=open(pdf,'rb')
            att = email.mime.application.MIMEApplication(fp.read(),_subtype="pdf")
            fp.close()
            att.add_header('Content-Disposition','attachment',filename=pdf)
            msg.attach(att)
        msg.attach(MIMEText(body_str, 'plain'))
        
        s = smtplib.SMTP('MAILHOST')
        s.starttls()
        s.sendmail(from_mail, merged_list, msg.as_string())
        s.quit()



    def get_users_from_groups(self, group_list):
        persons = self.people['person'].keys()
        user_list = []
        for person in self.people['person']:
            for group in group_list:
                for check in self.people['person'][person]['attr']['groups']:
                    if group == check:
                        user_list.append(person)
        user_set = sorted(set(user_list))
        return user_set
        

    def get_email_addresses_from_email_types(self, type_list, user_list):
        email_list = []
        for user in user_list:
            for mail_type in type_list:
                if mail_type == 'personal':
                    email_list.append(self.people['person'][user]['attr']['personal_email'])
                elif mail_type == 'work':
                    email_list.append(self.people['person'][user]['attr']['email'])
                else:
                    print("Email type must be either 'personal' or 'work'")
        email_set = sorted(set(email_list))
        return email_set


    def get_email_addresses_from_user_list(self, user_list):
        email_list = []
        for user in user_list:
            email_list.append(self.people['person'][user]['attr']['email'])
        email_set = sorted(set(email_list))
        return email_set


