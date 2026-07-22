"""
Utils is intended to be a swiss-army-knife toolbox that houses boilerplate codes
for many apps or scripts. A generic lib to access:
* config files,
* logs,
* email servers for notifications,
* [and maybe simple encryption, etc...]
"""
import base64
from datetime import datetime, timezone, timedelta
import json as jsonp
import logging
import os
from re import compile as re_compile
import requests
import warnings
from logging.handlers import RotatingFileHandler

try:
    import yaml  # 5.1.1+
except ImportError:
    yaml = None

__version__ = '1.23.4'

g = {}  # for global variables to be used across apps and scripts
UTILS_PART_OF_COMMON = True  # set True if this module is part of a common folder,
                             # (False, for standalone script)


def deprecated(func):
    def new_func(*args, **kwargs):
        warnings.warn(f"Call to deprecated function {func.__name__}.",
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
            if os.path.exists(f"{wd()}/config.json"):
                self.file = f"{wd()}/config.json"
            elif yaml and os.path.exists(f"{wd()}/config.yaml"):
                self.file = f"{wd()}/config.yaml"
            else:
                self.set_defaults()

        # -- read configs
        if self.file:
            if os.path.exists(self.file):
                self.read()
        return

    def file_type(self, change_to=None):
        """
        Change or return current file type.
        :param change_to: json or yaml
        :return: current file type
        """
        ft = 'memory'

        if not self.file:
            return ft

        t_split = self.file.split('.')
        t = t_split[len(t_split)-1]
        if isinstance(change_to, str):
            ft = change_to
            self.file = f"{'.'.join(t_split[:len(t_split)-1])}.{change_to}"
        else:
            if t == 'json':
                ft = 'json'
            elif t == 'yaml' or t == 'yml':
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
        fn = '[common.utils.Config][read]'
        if self.file_type() == 'memory':
            log.info(f"{fn} : config file is not set.")
            return

        with open(self.file, 'r') as f:
            if yaml and self.file_type() == 'yaml':
                self.params = yaml.load(f, Loader=yaml.FullLoader)
            else:
                self.params = jsonp.load(f)
            self._state = True
        return

    def __repr__(self):
        return jsonp.dumps(self.params, indent=4)

    def __setitem__(self, key, value):
        self.params[key] = value

    @deprecated
    def save(self):
        self.write()
        return

    def set(self, fp):
        self.file = fp

        # -- read configs
        if os.path.exists(self.file):
            self.read()
        return

    def set_defaults(self):
        self.params = {
            'service': {
                'app-name': 'app',
                'app-logs': None,
                'log-level': 'DEBUG',
                'log-stdout': True
            }
        }
        self._state = True
        return

    def status(self):
        return self._state

    def write(self):
        fn = '[common.utils.Config][write]'
        if self.file_type() == 'memory':
            log.info(f"{fn} : config file is not set.")
            return

        with open(self.file, 'w') as f:
            if yaml and self.file_type() == 'yaml':
                 yaml.dump(self.params, f, sort_keys=False)
            else:
                jsonp.dump(self.params, f, indent=4)
        return

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
            self._log_filename = f"{self._config['service']['app-logs']}/" \
                                 f"{self._config['service']['app-name']}.log"
            try:
                file_handler = RotatingFileHandler(self._log_filename, maxBytes=100*1024*1024, backupCount=3)
            except PermissionError:
                self._log_filename = f"/tmp/{self._config['service']['app-name']}.log"
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
        return jsonp.dumps(self.__dict__)

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


class OAuth2:
    """
    A typical implementation to obtain a token from an OAuth2 system.

    Usage: ...

    # -- initialize oauth
    http_session = requests.Session()
    oauth = OAuth2(token_keyname='access_token', exp_keyname='expires_in',
                   http_session=session)
    oauth.url = config['ipam']['api-url']
    oauth.ep.authen = f"{oauth.url}/login"

    # -- set http header and data field
    oauth.headers.apikey = config['ipam']['api-key']
    oauth.data.username = config['ipam']['username']
    oauth.data.password = config['ipam']['password']

    # -- send request to get token
    [oauth.handle_expiry(kind='timelapse')]
    [oauth.use_basic_authen(b64=True, data_omits=['username', 'password'])]
    [oauth.use_basic_authen()]
    [oauth.use_bearer()]
    oauth.get_token()

    # -- setup common endpoints
    oauth.ep.ip_address = f"{oauth.url}/Gets/getDeviceByIPAddr"
    oauth.ep.hostname = f"{oauth.url}/Gets/getDeviceByHostname"
    oauth.ep.mac_address = f"{oauth.url}/Gets/getDeviceByMACAddress"
    oauth.ep.start_address = f"{oauth.url}/Gets/getAddressPool"

    """
    # g['oauth'] = {'token': {}}
    class Data:
        def __repr__(self) -> str:
            return self.to_json()

        def to_dict(self) -> dict:
            return self.__dict__

        def to_json(self) -> str:
            return jsonp.dumps(self.__dict__, indent=4) if self.__dict__ else None

    class Endpoints:
        authen = None

    class Json:
        def __repr__(self) -> str:
            return self.to_json()

        def to_dict(self) -> dict:
            return self.__dict__

        def to_json(self) -> str:
            return jsonp.dumps(self.__dict__, indent=4) if self.__dict__ else None

    class Headers:
        __dict__ = {'Content-Type': 'application/json',
                    'Accept': 'application/json'}

        def __getattr__(self, key):
            return self.__dict__.get(key)

        def __repr__(self) -> str:
            return self.to_json()

        def __setattr__(self, key, value):
            self.__dict__[key] = value

        def to_dict(self) -> dict:
            return self.__dict__

        def to_json(self) -> str:
            return jsonp.dumps(self.__dict__, indent=4) if self.__dict__ else None

        def update(self, kv):
            if kv:
                for k, v in kv.items():
                    self.__setattr__(k, v)

    def __init__(self, http_session=None, token_type=None, token_keyname=None, exp_keyname=None) -> None:
        self._auth_basic_formencoded = False
        self._auth_basic_encoded = False
        self._auth_process = False
        self._bearer = False
        # self.credentials = None
        self.data = self.Data()
        self._data_omits = []
        self.ep = self.Endpoints()
        self.json = self.Json()
        self.headers = self.Headers()
        self.http_session = http_session if http_session else requests.Session()
        self.base_url = None
        self.api_url = None

        # -- standard oauth2 response
        self._access_token = None
        self._token_expires = None
        self._scope = None
        self._token_type = token_type if token_type else 'bearer'
        self._refresh_token = None

        # -- defaults
        self._token_keyname = token_keyname if token_keyname else 'access_token'
        self._exp_keyname = exp_keyname if exp_keyname else 'expires_in'
        self._exp_type = 'timelapse'  # other values: 'datetime', 'date'
        self.use_basic_authen()
        if token_type == 'bearer':
            self.use_bearer()
        return

    def _do_login(self, headers=None, data=None, json=None) -> tuple[object, Status]:
        fn = f"[common.utils.OAuth2][_do_login]"
        r = None
        s = Status(204, 'Nothing happened.')

        if not headers:
            headers = self.headers.to_dict()
        if not data:
            data = {}
            for k, v in self.data.to_dict().items():
                if k not in self._data_omits:
                    data[k] = v
            data = jsonp.dumps(data)
        if not json:
            json = self.json.to_json()

        try:
            if self._auth_process:
                if self._auth_basic_formencoded:
                    headers['Content-Type'] = 'application/x-www-form-urlencoded'
                if self._auth_basic_encoded and self.data.username and self.data.password:
                    credentials = base64.encodebytes(bytes(
                        f"{self.data.username}:{self.data.password}",
                        "utf-8")).decode("utf-8")
                    credentials = credentials.replace('\n', '')
                    log.debug(f"{fn} : Basic Auth Credentials: [{self.data.username}:{str(self.data.password)[:4]}****] => {credentials}")
                    headers['Authorization'] = f"Basic {credentials}"
            log.debug(f"{fn} : URL: {self.ep.authen}")
            log.debug(f"{fn} : headers: {headers}")
            log.debug(f"{fn} : data: {data}")
            log.debug(f"{fn} : json: {json}")
            res = None
            if self.ep.authen:
                log.info(f"{fn} : sending request to: {self.ep.authen}")
                res = self.http_session.post(self.ep.authen, headers=headers, data=data,
                    json=json, verify=False)
            log.debug(f"{fn} : response object (repr) : {res}")
            if res and res.status_code == 200:
                r = res.json()

                self._access_token = r[self._token_keyname] if r.get(self._token_keyname) else None
                self.handle_expiry(exp=r.get(self._exp_keyname))   # update self._token_expires
                self._scope = r['scope'] if r.get('scope') else None
                self._token_type = r['token_type'] if r.get('token_type') else None
                self._refresh_token = r['refresh_token'] if r.get('refresh_token') else None

                if self._token_type == 'bearer':
                    self.use_bearer()

                s.code = 200
                s.message = 'OK'
                if self._auth_process:
                    self.headers.__dict__['Content-Type'] = 'application/json'
                    self._auth_process = False
            else:
                s.code = res.status_code if res else 204
                s.message = f"{fn} : response: {res.text}" if res else f"{fn} : login request was not sent"
                log.info(s.message)
            del res
        except Exception as e:
            s.code = 500
            s.message = f"{fn} : error returned: {e}"
            log.error(s.message)
        return r, s

    def expired(self) -> bool:
        r = True
        # if isinstance(g['oauth'].get('expired_dt'), datetime) \
        #     and g['oauth']['expired_dt'] < datetime.now():
        if isinstance(self._token_expires, datetime) and \
            self._token_expires > datetime.now():
            r = False
        return r

    def get_token(self, token_keyname=None) -> dict:
        fn = f"[common.utils.OAuth2][get_token]"
        r = None

        # dt = ts(kind='date')
        if not token_keyname:
            token_keyname = self._token_keyname

        # -- validate token
        if not self.expired():
            # return g['oauth']['token']
            return self._access_token

        # g['oauth']['token'] = {}
        # g['oauth']['expired_dt'] = None
        self._access_token = None
        self._token_expires = None

        # -- or get new token
        try:
            self._auth_process = True
            res, res_status = self._do_login()
            if res and res.get(token_keyname):
                r = res.get(token_keyname)
                # self._access_token = g['oauth']['token'] = r
                log.debug(f"{fn} : {token_keyname}: {r}")
            else:
                log.error(f"{fn} : " \
                    f"Couldn't get token from API server.\nresponse: {res_status}")
        except Exception as e:
            log.error(f"{fn} : "\
                "Failed to get API token. Please verify all credentials." \
                f"\n{e}")

        if self._bearer and self._access_token:
            self.headers.Authorization = f"Bearer {self._access_token}"
        return r

    def handle_expiry(self, kind=None, exp=None):
        """
        kind: timelapse|datetime|date
        exp: {name: value}

        Example:
            oauth.handle_expiry()
            oauth.handle_expiry(kind='timelapse')
            oauth.handle_expiry(kind='timelapse', exp=3600)
            oauth.handle_expiry(kind='datetime', exp='2024-01-31T23:59:59')
            oauth.handle_expiry(kind='date', exp='2024-01-31')
        """
        fn = f"[common.utils.OAuth2][handle_expiry]"
        dt_fmt = '%Y-%m-%dT%H:%M:%SZ'
        msg_exp = ''

        if not kind:
            kind = self._exp_type if self._exp_type else 'timelapse'
        else:
            self._exp_type = kind
        if not exp:
            msg_exp = '(default)'
            # exp = 86400
            exp = 3600

        # -- timelapse
        if kind == 'timelapse' and str(exp).isdigit():
            # g['oauth']['expired_dt'] = datetime.now()+timedelta(seconds=exp)
            self._token_expires = datetime.now()+timedelta(seconds=exp)

        # -- date and datetime
        elif kind == 'date':
            dt_fmt = '%Y-%m-%dT%H:%M:%S'
            try:
                # g['oauth']['expired_dt'] = datetime.strptime(exp, dt_fmt)
                self._token_expires = datetime.strptime(exp, dt_fmt)
            except:
                try:
                    # g['oauth']['expired_dt'] = datetime.strptime(exp[:10], dt_fmt)
                    self._token_expires = datetime.strptime(exp[:10], dt_fmt)
                except:
                    msg_exp = '(default)'
                    log.error(f"{fn} : Could not parse expiration timeframe. (set: 24hrs){msg_exp}")
                    # g['oauth']['expired_dt'] = datetime.now()+timedelta(days=1)
                    self._token_expires = datetime.now()+timedelta(days=1)

        # -- ??? from token
        else:
            ...  #ToDo:

        # g['oauth']['expiry_type'] = kind
        # log.info(f"{fn} : token expires on {datetime.strftime(g['oauth']['expired_dt'], dt_fmt)} {msg_exp}")
        if self._token_expires:
            log.info(f"{fn} : token expires on {datetime.strftime(self._token_expires, dt_fmt)} {msg_exp}")
        else:
            log.error(f"{fn} : token expiration isnot set")
        return

    def use_basic_authen(self, b64=False, data_omits=None, via_form=True):
        self._auth_basic_formencoded = via_form
        if b64:
            self._auth_process = True
            self._auth_basic_encoded = True
        if isinstance(data_omits, list):
            self._data_omits = data_omits
        self._do_login()

    def use_bearer(self, set_to=True):
        if set_to and not self._token_type:
            self._token_type = 'bearer'
        self._bearer = set_to


def envar(txt) -> str:
    """
    Returns environent variable value (if exists).
    """
    return os.environ.get(txt) if txt else None


def envar_in(txt) -> str:
    """
    Returns environment variable value and replace in string.
    """
    r = None
    if isinstance(txt, str) and '((env:' in txt and '))' in txt:
        s = txt.index('((env:')
        e = txt.index('))')
        v = txt[s:e+2]
        t = os.environ.get(v.replace('((env:', '').replace('))', ''))
        if t:
            r = txt.replace(v, t)
        del s, e, v, t, txt
    return r if r else txt


def do_get(url, data=None, http_session=None, verify_https=False) -> tuple[object, Status]:
    return do_requests('GET', url=url, http_session=http_session, data=data, verify_https=verify_https)


def do_post(url, headers=None, data=None, json=None, http_session=None, verify_https=False) -> tuple[object, Status]:
    return do_requests('POST', url=url, http_session=http_session, headers=headers, data=data, json=json, verify_https=verify_https)


def do_requests(method, url, http_session=None, headers=None, data=None, json=None, verify_https=False) -> tuple[object, Status]:
    fn = '[common.utils][do_request]'
    r = None
    s = Status(204, 'Nothing happened.')
    http_session = http_session if http_session else requests.Session()

    hd = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    if headers is None:
        headers = {}
    hd.update(headers)

    res = None
    log.debug(f"{fn} : URL: {url}")
    log.debug(f"{fn} : headers: {hd}")

    # -- validate url
    pattern = re_compile(r'^https:\/\/[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})+\/[^\s?]+(?:\?[^\s]+)?$')
    if not pattern.match(url):
        s.code = 400
        s.message = 'Bad URL.'
        log.error(f"{fn} : {s.message} : {url}")
        return r, s

    if method == 'GET':
        log.info(f"{fn} : [GET] {url}")
        res = http_session.get(url, headers=hd, params=data, verify=verify_https)
        if res.status_code == 200:
            r = res.json() if res.json() else res.text
            if not r:
                s.code = 404
                s.message = 'No Data.'
            else:
                s.code = 200
                s.message = 'OK.'
        else:
            s.code = res.status_code
            s.message = f'Error: {res.text}'
    elif method == 'POST':
        log.info(f"{fn} : [POST] {url}")
        res = http_session.post(url, headers=hd, data=data, json=json, verify=verify_https)
        if res.status_code in [200, 201]:
            r = res.json() if res.json() else res.text
            s.code = res.status_code
            s.message = '[POST] successful.'
        else:
            s.code = res.status_code
            s.message = f'Error: {res.text}'
    else:
        s.message = 'HTTP method is currently not supported.'
    log.info(f"{fn} : message : {s.message}")
    del res

    log.debug(f"{fn} : returns {r}")
    return r, s


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


def rwjson(action, key_fn) -> None:
    """
    This function automatically creates a local json file based on the key name.
    To access the data also import "g" the module variable.
    :param action: pass "read" or "write" as action to be performed
    :param key_fn: key name provided will be also the local filename
    """
    g.setdefault(key_fn, None)
    # -- override default parameters
    if not g.get('_rwpath'):
        g['_rwpath'] = wd()
    if not g.get('_rwfn'):
        g['_rwfn'] = f"_{key_fn}.json"
    # -- known behaviors
    if action == 'read':
        try:
            with open(f"{g['_rwpath']}/{g['_rwfn']}", 'r') as f:
                g[key_fn] = jsonp.load(f)
        except:
            pass
    if action == 'write':
        with open(f"{g['_rwpath']}/{g['_rwfn']}", 'w') as f:
            jsonp.dump(g[key_fn], f)
    return


def ts(kind=None, ret=None, from_dt=None, from_ts=None, from_obj=None, from_pattern=None) -> object:
    """
    Provide the current timestamp in various formats.
    :param kind: (deprecated, same as ret)
    :param ret: string to describe expected return value type (default: iso8601)
    :param from_dt: use string as input
    :param from_ts: use int[timestamp] as input
    :param from_pattern: use string as input
    :return: object|string
    Example:
        ts(ret='date', from_dt='2024-01-31T23:59:59')
        ts(ret='object', from_dt='2024-01-31T23:59:59')
        ts(ret='iso8601', from_ts=1234567890)
        ts(from_obj=datetime.now(timezone.utc))
        ts(from_pattern='%Y-%m-%d %H:%M:%S', from_dt='2024-01-31 23:59:59')
    """
    fn = '[common.utils][ts]'
    r = None

    if not from_pattern:
        from_pattern = '%Y-%m-%dT%H:%M:%SZ'

    try:
        # -- get datetime object
        if not from_dt and not from_ts and not from_obj:
            dt = datetime.now(timezone.utc)
        elif from_obj:
            dt = from_obj
        elif from_dt:
            dt = datetime.strptime(from_dt, from_pattern)
        elif from_ts:
            dt = datetime.fromtimestamp(from_ts, timezone.utc)

        # -- set return value
        if kind == 'date' or ret == 'date':
            r = datetime.strftime(dt, '%Y-%m-%d')
        elif kind == 'object' or ret == 'object':
            r = dt
        elif not kind or not ret or ret == 'iso8601':
            r = datetime.strftime(dt, from_pattern)
    except Exception as e:
        log.error(f"{fn} : {e}")
    return r


def wd():
    """
    Provide the Working Directory where the auto_utils script is located.
    :return wd: string description
    """
    app_root = '/..' if UTILS_PART_OF_COMMON else ''
    path = os.path.realpath(f"{__file__}{app_root}").split('/')
    return '/'.join(path[:len(path)-1])


log = Log()
config = Config()
