#coding=utf-8

#from distutils.core import setup
from setuptools import setup

setup(
    name = 'exception_mail',
    version = '0.0.1',
    packages = ['exception_mail'],
    install_requires = ['tornado'],
    author = 'letv gcp',
    author_email = 'liujinliu@le.com',
    description = 'suitable for sending program exception via email',
    entry_points = {
        'console_scripts':[
            'exception_email_start=exception_mail.cmd:main'
            ]
        }
    )
