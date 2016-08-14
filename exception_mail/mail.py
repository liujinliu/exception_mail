#coding=utf-8
import os
import re
import logging
import time
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE
from email.utils import formatdate
import hashlib
from tornado.gen import Task
import datetime
from mail_session import SMTPSession
from tornado.escape import utf8
from concurrent.futures import ThreadPoolExecutor
from tornado.ioloop import PeriodicCallback

thread_pool = ThreadPoolExecutor(2)

# borrow email re pattern from django
_email_re = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'  # quoted-string
    r')@(?:[A-Z0-9]+(?:-*[A-Z0-9]+)*\.)+[A-Z]{2,6}$', re.IGNORECASE)  # domain

class EmailAddress(object):
    def __init__(self, addr, name=""):
        assert _email_re.match(addr), "Email address(%s) is invalid." % addr

        self.addr = addr
        if name:
            self.name = name
        else:
            self.name = addr.split("@")[0]

    def __str__(self):
        return '%s <%s>' % (utf8(self.name), utf8(self.addr))

class MailEgine(object):
    
    def __init__(self, interval = 10):
        #including the md5 sum of mail content
        self.mails = {}
        self.interval = interval
        self.session = SMTPSession

    def egine_fire_start(self, host, port, user='',
                        password='', duration=30,
                        tls=False):
        self.session.connect(host, port, user='',
                        password='', duration,
                        tls)
        PeriodicCallback(self.mail_scan_work,
                        interval * 60000).start()

    def _mail_address_filter(self, mailfrom, to):
        if isinstance(mailfrom, EmailAddress):
            mailfrom = str(mailfrom)
        else:
            mailfrom = utf8(mailfrom)
        to = [utf8(t) for t in to]
        mtlist = []
        for mail in to:
            for t in re.split(';|,', mail):
                mtlist.append(t)
        mailto = []
        for mt in mtlist:
            if re.match('\S*\s*<\s*\S+@\S+\.\S+>', mt):
                mailto.append(mt)
        return mailfrom, mailto

    def _mail_attachment(self, outer, filenames):
        filename_list = filenames.split(',')
        for filename in filename_list:
            file_part = MIMEText(open(filename,'rb').read())
            file_part.add_header('Content-Disposition',
                    'attachment',filename=filename)
            outer.attach(file_part)

    def mail_report(mailfrom, to, subject, body, md5_value,
                    attachments = [], html = None):
        if html:
            message = MIMEMultipart("alternative")
            message.attach(MIMEText(body, "plain"))
            message.attach(MIMEText(html, "html"))
        else:
            message = MIMEText(body)
        if attachments:
            part = message
            message = MIMEMultipart("mixed")
            message.attach(part)
            for filename, data in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(data)
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", "attachment",
                    filename=filename)
                message.attach(part)
    
        message["Date"] = formatdate(time.time())
        message["From"] = fr
        message["To"] = COMMASPACE.join(to)
        message["Subject"] = '%s_%s' %(md5_value, utf8(subject))
        return message 

    def _mail_md5(self, mail_from, to, subject, content):
        src = '%s%s%s%s' %(mail_from, to, subject, content)
        myMd5 = hashlib.md5()
        myMd5.update(src)
        return myMd5.hexdigest()

   def _mail_record(self, md5_value, mail_from,
                    to, subject):
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

    def _send(self, fr, to, message):
        self.session.send_mail(fr, mailto, utf8(message.as_string()))
    def send_email(self, mailfrom, to, subject, body,
                    html=None, attachments=[]):
        fr, mailto = self._mail_address_filter(mailfrom, to)
        md5_value = self._mail_md5(mail_from, to, body)
        if not self._should_send(md5_value)
            logging.info(('too much email from %s to %s,'
                         'subject:%s, body md5:%s')
                    %(mail_from, mail_to, md5_value))
            return
        message = self.mail_report(mailfrom, to, subject, body,
                                md5_value, attachments, html)
        try:
            logging.info(('send email from %s to %s succeed,'
                           'subject:%s, mail body is:\n%s')
                           %(mailfrom, to, subject, body))
            self._send(fr, mailto, utf8(message.as_string()))
            self._mail_record(md5_value, mail_from, to, subject)
        except Exception as e:
            logging.error(('send email from %s to %s failed,'
                           'subject:%s, mail body is:\n%s')
                           %(mail_from, to, subject, body))
            loggine.error(e, exc_info = True)

    def _ok_mail_build(self):
        now = datetime.datetime.now()
        for md5_values in self.mails:
            last_time = self.mails[md5_values]['sendtime']
            if (now-last_time).minutes < self.interval:
                continue
            mail_dict = self.mails[md5_value]
            mailfrom = mail_dict['mail_from']
            to = mail_dict['to']
            subject = 'OK--%s' %mail_dict['subject']
            body = 'DONOT WORRY'
            fr, mailto = self._mail_address_filter(mailfrom, to)
            yield dict(md5_value = md5_value,
                       mailfrom = fr,
                       mailto = mailto,
                       email = self.mail_report(mail_from, mailto,
                                      subject, body, md5_value))
    
    def mail_scan_work(self):
        Task(thread_pool.submit, self._ok_mail_send)

    def _ok_mail_send(self):
        for mails in self._ok_mail_build():
            try:
                self._send(mails['mailfrom'],
                        mails['mailto'],
                        utf8(mails['email'].as_string()))
                del self.mails[mails['md5_value']
            except Exception as e:
                logging.info('send OK email failed, md5:%s',
                             mails['md5_value'])
                logging.error(e, exc_info=True)

