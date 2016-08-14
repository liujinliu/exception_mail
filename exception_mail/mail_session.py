#coding=utf-8
import logging
import smtplib
import time
from datetime import datetime, timedelta

class _SMTPSession(object):
    def __init__(self):
        self.session = None

    def connect(self, host, port, user='',
                password='', duration=30,
                tls=False):
        self.renew()
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.duration = duration
        self.smtp_tls = tls
        self.deadline = datetime.now()
        self.renew()

    def send_mail(self, fr, to, message):
        if self.timeout:
            self.renew()

        try:
            self.session.sendmail(fr, to, message)
        except Exception, e:
            logging.error(e, exc_info=True)
            err = "Send email from %s to %s failed!\n Exception: %s!" \
                % (fr, to, e)
            logging.error(err)
            self.renew()

    @property
    def timeout(self):
        return self.deadline <= datetime.now()

    def renew(self):
        try:
            if self.session:
                self.session.quit()
        except Exception:
            logging.error(e, exc_info=True) 

        self.session = smtplib.SMTP(self.host, self.port)
        if self.user and self.password:
            if self.smtp_tls:
                self.session.starttls()
            self.session.login(self.user, self.password)

        self.deadline = datetime.now() + timedelta(
                        seconds=self.duration * 60)

_SMTPSession = _SMTPSession()
