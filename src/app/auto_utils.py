"""
Utils is intended to be a swiss-army-knife toolbox that houses boilerplate codes
for many apps or scripts. A generic lib to access:
* config files,
* logs,
* email servers for notifications,
* [and maybe simple encryption, etc...]
"""

from dataclasses import dataclass
import json
import logging
import os
import warnings
from logging.handlers import RotatingFileHandler


try:
    import yaml  # 5.1.1+
except ImportError:
    yaml = None


__authors__ = ['randollrr', 'msmith8']
__version__ = '1.17'


def deprecated(func):
    def new_func(*args, **kwargs):
        warnings.warn("Call to deprecated function {0}.".format(func.__name__),
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    new_func.__name__ = func.__name__
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
            elif yaml and os.path.exists('{}/config.yaml'.format(wd())):
                self.file = '{}/config.yaml'.format(wd())

        # -- read configs
        if self.file:
            if os.path.exists(self.file):
                self.read()

    def file_type(self):
        """
        Check file type: json or yaml
        """
        ft = 'json'

        t = self.file.split('.')[len(self.file.split('.'))-1]
        if t == 'yaml' or t == 'yml':
            ft = 'yaml'
        return ft

    def __getitem__(self, item):
        r = {}
        try:
            r = self.params[item]
            if isinstance(r, dict):
                for k, v in r.items():
                    r[k] = envar_in(v)
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

    @deprecated
    def save(self):
        self.write()

    def set(self, fp):
        self.file = fp

        # -- read configs
        if os.path.exists(self.file):
            self.read()

    def status(self):
        return self._state

    def write(self):
        with open(self.file, 'w') as f:
            if yaml and self.file_type() == 'yaml':
                 yaml.dump(self.params, f)
            else:
                json.dump(self.params, f, indent=4)


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

    def logfn(self):
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
        if self.logfn():
            with open(self.logfn(), 'w'):
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
    """
    ToDo: redesign/re-implement
    """

    def __init__(self, from_addr=None, to_addr=None, subject=None, body=None):
        self.from_addr = None
        self.to_addr = None

    def attach(self):
        ...

    def create_message(self):
        ...

    def send(self, message):
        ...

    def set_mime(self, msg_body, mimetype='html'):
        ...


@dataclass
class Status:
    """
    Status codes for APIs

    [default text] This API is designed to return different status codes:

    * 200 (OK, done)[POST, GET, PUT, DELETE]:
        The request was successful, the resource(s) itself is returned as
        JSON by default

    * 204 (nothing happened)[POST, PUT, DELETE]:
        Requested action was not understood or recognized

    * 400 (bad request, missing values, required fields are missing, missing
        permission/authentication)[POST, GET, PUT, DELETE]:

    * 404 (requested items not found, data not found)[GET]:
        A resource could not be accessed (e.g. a check ID could not be found)

    * 500 (service error, handled exception occurred)[POST, GET, PUT, DELETE]:
        Something went wrong on the server side (e.g. a check could not be saved
        in database)
    """
    code = None
    message = None

    def __init__(self, code, message) -> None:
        self.__dict__['code'] = code
        self.__dict__['message'] = message

    def __repr__(self) -> str:
        """
        Returns printable string representation of this object.
        """
        return json.dumps(self.__dict__)

    def to_dict(self) -> dict:
        """
        Returns dict representation of this object.
        """
        return self.__dict__

    def to_str(self) -> str:
        """
        Returns string representation of this object.
        """
        return self.__repr__()


def envar_in(txt):
    r = txt
    if isinstance(txt, str) and '((env:' in txt and '))' in txt:
        txt = txt.replace(' ', '')
        s = txt.index('((env:')
        e = txt.index('))')
        v = txt[s:e+2]
        t = os.environ.get(v.replace('((env:', '').replace('))', ''))
        if t:
            r = txt.replace(v, t)
            del s, e, v, t, txt
    return r


def next_add(text):
    r = None

    def digits(_t):
        _r = None
        if isinstance(_t, str):
            _cnt = 0
            for _c in ''.join(reversed(_t)):
                if _c.isdigit():
                    _cnt += 1
                else: break
            _r = _cnt
        return _r

    n = digits(text)
    r = f"{text[:-n]}{str(int(text[-n:])+1).zfill(n)}" if n else text

    return r


def wd():
    """
    Provide the Working Directory where the auto_utils script is located.
    :return wd: string description
    """
    path = os.path.realpath(__file__).split('/')
    return '/'.join(path[:len(path)-1])


log = Log()
config = Config()
