#!/usr/bin/env python

from sys import argv
from getpass import getpass
import json
from os import environ
import time

import requests

# from auto_utils import log

__version__ = '1.0.5'


class Log:
    def info(self, txt):
        print(f'- {txt}')

    def error(self, txt):
        print(f'- {txt}')


class Authentication:
    """
    UMS client token "requester" mostly for testing.
    """
    def __init__(self, authen_fn=None, username=None, passwd=None):
        self.obj = None
        self.authen_fn = './authen.json' if not authen_fn else authen_fn
        self.reset()
        self.get_token(username, passwd)

    def _fscache(self, action):
        """
        Retrieve/create "./authen.json" file.
        """
        log.info('Get local cached token.')

        # -- load authentication from filesystem caching
        if action == 'load':
            try:
                with open(self.authen_fn, 'r') as f:
                    self.obj = json.load(f)
            except:
                log.error(f"{self.authen_fn} file not found.")

        # -- save new authentication creds in cache file (authen.json)
        elif action == 'save':
            if self.obj:
                with open(self.authen_fn, 'w') as f:
                    json.dump(self.obj, f)

    def __getitem__(self, item):
        return self.obj.get(item)

    def get_token(self, username, passwd):
        """
        Get token from UMS REST service.
        """
        log.info('Request token from UMS server.')

        def _validate():
            _r = False
            _ts = int(time.mktime(time.gmtime()))
            if self.obj.get('token_payload') and \
                self.obj['token_payload']['exp'] < _ts:
                    log.info('Reset: token expired.')
                    self.reset()
            elif self.obj.get('access_token') and not self.obj.get('hearders'):
                self.obj['headers'] = {
                    'Authorization': f"Bearer {self.obj['access_token']}",
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'}
            if self.obj.get('headers'):
                log.info('Current token is valid.')
                _r = True
            return _r

        # -- validate token
        if not _validate():
            self._fscache('load')
            _validate()

        if self.obj.get('headers'):
            return self.obj

        # -- get username and password from environment
        if not self.obj.get('headers') and not username or not passwd:
            log.info('Getting username and password from environment variable.')
            username = environ.get('_U')
            passwd = environ.get('_P')

        if not self.obj.get('headers') and username and passwd:
            log.info('sending request.')
            res = requests.post(
                'https://authenticate.coxsweng.com/api/login/no_aud',
                auth=(username, passwd))
            if res.status_code == 200:
                self.obj = res.json()
                self._fscache('save')
                log.info('successful!')
            else:
                log.error('failed.')
        else:
            log.error('Usename and password are required.')
            self.usage()

    def reset(self):
        self.obj = {'headers': {}}

    def usage(self):
        log.info(
            'usage...\n\n'
            'auto_ums.py -u <username> -p [password]\n'
            '    -u username\n'
            '    -p password or leave blank for prompt\n\n'
            '(note: if switches are mising, environment variable will be used.)\n')


log = Log()


if __name__ == '__main__':
    u = None
    p = None
    if len(argv)>=2:
        if '-u' in argv:
            u = argv[argv.index('-u')+1]
        if '-p' in argv:
            p = getpass()
    authen = Authentication(username=u, passwd=p)
else:
    authen = Authentication()


# v1.0.3 added __getitem__() to object
#        added CLI support for username and password
# v1.0.4 added usage()
# v1.0.5 remove dependency on auto_utils log object
