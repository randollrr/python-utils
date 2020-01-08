"""
Utils is intended to be a swiss-army-knife toolbox that houses boilerplate codes
for many apps or scripts. A generic API to access:
* config files,
* logs,
* email servers for notifications,
* [and maybe simple encryption, etc...]

"""
__authors__ = ['randollrr', 'msmith8']
__version__ = '1.11'

import json
import logging
import os
import warnings
from logging.handlers import RotatingFileHandler

yaml = None
try:
    import yaml
except ImportError:
    pass


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""
    def new_func(*args, **kwargs):
        warnings.warn("Call to deprecated function {0}.".format(func.__name__),
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func


class Config:
    """
    Read and write configuration file(s). 2015.06.19|randollrr
    * specify UTILS_CONFIG_FILE envar for "config.yaml"
    """
    def __init__(self, fname=None):
        self._state = False
        self.params = None
        self.file = fname

        # -- check name of config file
        if not self.file:
            if os.path.exists('{}/config.json'.format(wd())):
                self.file = '{}/config.json'.format(wd())
            elif yaml and os.path.exists('{}/config.yaml').format(wd()):
                self.file = '{}/config.yaml'.format(wd())

        # -- read configs
        if self.file:
            if os.path.exists(self.file):
                self.read()

    def file_type(self):
        # -- check file type: json or yaml
        ft = 'json'
        if len(self.file.split('.')) > 1:
            t = self.file.split('.')[1]
            if t == 'yaml' or t == 'yml':
                ft = 'yaml'
        return ft

    def __getitem__(self, item):
        r = None
        try:
            r = self.params[item]
        except Exception:
            pass
        return r

    def read(self):
        with open(self.file, 'r') as f:
            if yaml and self.file_type() == 'yaml':
                self.params = yaml.load(f, Loader=yaml.FullLoader)
            else:
                self.params = json.load(f)
            self._state = True

    def __repr__(self):
        return json.dumps(self.params, indent=4)

    def __setitem__(self, key, value):
        self.params[key] = value

    def save(self):
        with open(self.file, 'w') as f:
            if yaml and self.file_type() == 'yaml':
                 yaml.dump(self.params, f)
            else:
                json.dump(self.params, f, indent=4)

    def set(self, fp):
        self.file = fp

        # -- read configs
        if os.path.exists(self.file):
            self.read()

    def status(self):
        return self._state


class Log:
    """
    Logging wrapper class for apps and scripts. 2016.02.10|randollrr
    """
    def __init__(self):
        self.DEBUG = logging.DEBUG
        self.INFO = logging.INFO
        self.ERROR = logging.ERROR
        self.WARN = logging.WARN
        self.logger = None
        self.handlers = {'file': None, 'screen': None}
        self._log_filename = None

        self._config = Config()
        if self._config.status():
            self.set_logger()

    def addhandler(self, handler):
        self.logger.addHandler(handler)

    def config(self, conf):
        self._config = conf
        if self._config.status():
            self.set_logger()

    def debug(self, msg):
        if not self._config.status():
            self.set_logger()
        self.logger.debug(msg)

    def error(self, msg):
        if not self._config.status():
            self.set_logger()
        self.logger.error(msg)

    def filename(self):
        return self._log_filename

    def gethandler(self):
        r = self.logger.handlers
        if self.handlers['file']:
            r = self.handlers['file']
        elif self.handlers['screen']:
            r = self.handlers['screen']
        return r

    def info(self, msg):
        if not self._config.status():
            self.set_logger()
        self.logger.info(msg)

    def reset(self):
        if self.filename():
            with open(self.filename(), 'w'):
                pass

    def set_logger(self, svcname=None):
        log_level = self._config['service']['log-level']
        if log_level == "DEBUG":
            level = self.DEBUG
        elif log_level == "INFO":
            level = self.INFO
        elif log_level == "ERROR":
            level = self.ERROR
        elif log_level == "WARN":
            level = self.WARN
        else:
            level = self.DEBUG
        if svcname:
            self.logger = logging.getLogger(svcname)
        else:
            self.logger = logging.getLogger(self._config['service']['app-name'])
        self.logger.setLevel(level)
        formatter = logging.Formatter('[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S +0000')
        # -- file based logging
        if self._config['service']['app-logs']:
            try:
                self._log_filename = '{}/{}.log'.format(self._config['service']['app-logs'],
                                                    self._config['service']['app-name'])
                file_handler = RotatingFileHandler(self._log_filename, maxBytes=100*1024*1024, backupCount=3)
            except PermissionError:
                self._log_filename = '/tmp/{}.log'.format(self._config['service']['app-name'])
                file_handler = RotatingFileHandler(self._log_filename, maxBytes=100*1024*1024, backupCount=3)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.handlers['file'] = file_handler

        # -- on-screen/stdout logging
        if self._config['service']['log-stdout']:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)
            self.handlers['screen'] = stream_handler

    def warn(self, msg):
        self.logger.warning(msg)


class Email:
    """A simple client to send email via a local sendmail instance
    """
    def __init__(self):
        global config
        config = Config()
        self.SENDMAIL = config['service']['sendmail']
        self.from_addr = self.SENDMAIL['from']
        self.to_addresses = self.SENDMAIL['to']

    def send_email(self, subject, body):
        p = os.popen('/usr/sbin/sendmail -t', 'w')
        p.write('To: {}\n'.format(self.to_addresses))
        p.write('Subject: {}\n'.format(subject))
        p.write('From: {}\n'.format(self.from_addr))
        p.write('\n')  # blank line separating headers from body
        p.write(body)
        sts = p.close()
        if sts != 0:
            log.info('Sendmail exit status: {}'.format(sts))


def wd():
    """
    Provide the Working Directory where the auto_utils script is located.
    :return wd: string description
    """
    path = os.path.realpath(__file__).split('/')
    return '/'.join(path[:len(path)-1])


log = Log()
config = Config()
