#coding=utf-8
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import sys
import hashlib
import datetime
import logging

class MailEgine(object):
    
    def __init__(self, interval = 10):
        #including the md5 sum of mail content
        self.mails = {}
        self.interval = interval

    def _mail_attachment(self, outer, filenames):
        filename_list = filenames.split(',')
        for filename in filename_list:
            file_part = MIMEText(open(filename,'rb').read())
            file_part.add_header('Content-Disposition',
                    'attachment',filename=filename)
            outer.attach(file_part)

    def mail_report(mailfrom, to, subject,
                   content, filenames = None):
        outer = MIMEMultipart()
        outer['Subject'] = subject
        outer['From'] = mailfrom 
        outer['To'] = to
        # Internal text container
        inner = MIMEMultipart('alternative')
        part1 = MIMEText(content,'plain')
        inner.attach(part1)
        outer.attach(inner)
        if filenames:
            self._mail_attachment(outer, filenames)
        return outer

    def _mail_md5(self, mail_from, to, subject, content):
        src = '%s%s%s%s' %(mail_from, to, subject, content)
        myMd5 = hashlib.md5()
        myMd5.update(src)
        return myMd5.hexdigest()

   def _mail_record(self, md5_value, mail_from,
                    to, subject, smtp_server):
        if not self.mails.has_key(md5_value):
            self.mails[md5_value] = dict(
                mail_from = mail_from,
                to = to,
                subject = subject)

    def _should_send(self, md5_value):
        now = datetime.datetime.now()
        if self.mails.has_key(md5_value):
            last_time = self.mails[md5_value]['sendtime']
            time_pass = now - last_time
            return time_pass.minutes > self.interval
        return True

    def _send_message(self, message, smtp_addr,
                    userlogin, userpass):
        s = smtplib.SMTP(smtp_addr)
        s.login(userlogin, userpass)
        s.sendmail(message['From'], 
                   message['To'].split(','),
                   message.as_string())
        s.close()
    
    def send_email(self, smtp_server, mail_from, to,
                   subject, content, user_pass, filenames=None):
        md5_value = self._mail_md5(mail_from, to, content)
        if not self._should_send(md5_value)
            logging.info(('too much email from %s to %s,'
                         'subject:%s, content md5:%s')
                    %(mail_from, mail_to, md5_value))
            return
        email = self.mail_report(mail_from, to, subject, content,
                                 filenames)
        try:
            logging.error(('send email from %s to %s succeed,'
                           'subject:%s, mail content is:\n%s')
                           %(mail_from, to, subject, content))
            self._send_message(email, smtp_server, mail_from, userpass)
            self._mail_record(md5_value, mail_from, to, subject, smtp_server)
        except Exception as e:
            logging.error(('send email from %s to %s failed,'
                           'subject:%s, mail content is:\n%s')
                           %(mail_from, to, subject, content))
            loggine.error(e, exc_info = True)

    def _ok_mail_build(self):
        now = datetime.datetime.now()
        for md5_values in self.mails:
            last_time = self.mails[md5_values]['sendtime']
            if (now-last_time).minutes < self.interval:
                continue
            mail_dict = self.mails[md5_value]
            mail_from = mail_dict['mail_from']
            to = mail_dict['to']
            subject = 'OK--%s' %mail_dict['subject']
            content = 'DONOT WORRY'
            yield dict(md5_value = md5_value,
                       smtp_server = mail_dict['smtp_server'],
                       mail_from = mail_from,
                       userpass = mail_dict['user_pass'],
                       email = self.mail_report(mail_from, to,
                                subject, content))

    def _ok_mail_send(self, smtp_server):
        for mails in self._ok_mail_build():
            try:
                self._send_message(mails['email'],
                        mails['smtp_server'],
                        mails['mail_from'],
                        mails['userpass'])
                del self.mails[mails['md5_value']
            except Exception as e:
                logging.info('send OK email failed, md5:%s',
                             mails['md5_value'])
                logging.error(e, exc_info=True)


