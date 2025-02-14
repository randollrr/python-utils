import base64
from datetime import datetime, timedelta
import json

from common.utils import config, log, ts, Status
from requests import Session
import urllib3
urllib3.disable_warnings()

__version__ = '2.0.0'
_g = {'token': {}}


class Oauth:
    """
    A typical implementation to obtain a token from an Oauth2 system.
    """

    class Data:
        def __repr__(self) -> str:
            return self.to_json()

        def to_dict(self) -> dict:
            return self.__dict__

        def to_json(self) -> str:
            return json.dumps(self.__dict__, indent=4) if self.__dict__ else None

    class Endpoints:
        authen = '/authenticate'

    class Json:
        def __repr__(self) -> str:
            return self.to_json()

        def to_dict(self) -> dict:
            return self.__dict__

        def to_json(self) -> str:
            return json.dumps(self.__dict__, indent=4) if self.__dict__ else None

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
            return json.dumps(self.__dict__, indent=4) if self.__dict__ else None

        def update(self, kv):
            if kv:
                for k, v in kv.items():
                    self.__setattr__(k, v)

    def __init__(self, http_session=None, token_keyname=None) -> None:
        self._auth_basic_type = False
        self._auth_basic_encoded = False
        self._auth_process = False
        self._bearer = False
        # self.credentials = None
        self.data = self.Data()
        self._data_omits = []
        self.ep = self.Endpoints()
        self.jsonObj = self.Json()
        self.headers = self.Headers()
        self.http_session = http_session if http_session else Session()
        self._token = None
        self._token_keyname = token_keyname if token_keyname else 'access_token'
        self.url = None

    def _do_login(self, headers=None, data=None, jsonObj=None) -> tuple[object, Status]:
        fn = f"[oauth][_do_login]"
        r = None
        s = Status(204, 'Nothing happened.')

        if not headers:
            headers = self.headers.to_dict()
        if not data:
            data = {}
            for k, v in self.data.to_dict().items():
                if k not in self._data_omits:
                    data[k] = v
        if not jsonObj:
            jsonObj = self.jsonObj.to_json()

        log.info(f"{fn} : sending request to: {self.ep.authen}")
        try:
            if self._auth_process:
                if self._auth_basic_type:
                    headers['Content-Type'] = 'application/x-www-form-urlencoded'
                if self._auth_basic_encoded:
                    credentials = base64.encodebytes(bytes(
                        f"{config['ipcontrol']['username']}:{config['ipcontrol']['password']}",
                        "utf-8")).decode("utf-8")
                    headers['Authorization'] = f"Basic {credentials[:-1]}"
            log.debug(f"{fn} : hearders: {headers}")
            log.debug(f"{fn} : data: {data}")
            log.debug(f"{fn} : json: {jsonObj}")
            res = self.http_session.post(self.ep.authen, headers=headers, data=data,
                json=jsonObj, verify=False)
            if res and res.status_code == 200:
                r = res.json()
                s.code = 200
                s.message = 'OK'
                if self._auth_process:
                    self.headers.__dict__['Content-Type'] = 'application/json'
                    self._auth_process = False
            else:
                s.code = res.status_code
                s.message = f"{fn} : response: {res.text}"
            del res
        except Exception as e:
            s.code = 500
            s.message = f"{fn} : error returned: {e}"
            log.error(s.message)
        return r, s

    def expired(self) -> bool:
        r = True
        if isinstance(_g.get('expired_dt'), datetime) \
            and _g['expired_dt'] < datetime.now():
            r = False
        if _g.get('expiry_type') and _g['expiry_type']:
            ...
        return r

    def get_token(self, token_keyname=None) -> dict:
        fn = f"[oauth][get_token]"
        r = None

        # dt = ts(kind='date')
        if not token_keyname:
            token_keyname = self._token_keyname

        # -- validate token
        if not self.expired():
            return _g['token']
        _g['token'] = {}
        _g['expired_dt'] = None

        # -- or get new token
        try:
            self._auth_process = True
            res, res_status = self._do_login()
            if res:
                r = res.get(token_keyname)
                self._token = _g['token'] = r
                log.debug(f"{fn} : {token_keyname}: {r}")
            else:
                log.error(f"{fn} : " \
                    f"Couldn't get token from API server.\nresponse: {res_status}")
        except Exception as e:
            log.error(f"{fn} : "\
                "Failed to get API token. Please verify all credentials." \
                f"\n{e}")

        if self._bearer and self._token:
            self.headers.Authorization = f"Bearer {self._token}"
        return r

    def handle_expiry(self, kind=None, exp={}):  # ToDo: ...
        """
        kind: timelapse|date
        key_value: {name: value}
        Example:
            oauth.handle_expiry(kind='timelapse', exp=3600)
            oauth.handle_expiry(kind='keyname', exp='expires_in')  # from token
            oauth.handle_expiry(kind='date', exp='2024-01-31T23:59:59')
            oauth.handle_expiry(kind='date', exp='2024-01-31')
        """
        fn = f"[oauth][handle_expiry]"
        dt_fmt = '%Y-%m-%dT%H:%M:%SZ'
        msg_exp = ''

        if not kind:
            kind = 'timelapse'
        if not exp:
            msg_exp = '(default)'
            exp = 86400

        # -- timelapse
        if kind == 'timelapse':
            _g['expired_dt'] = datetime.now()+timedelta(seconds=exp)

        # -- date
        elif kind == 'date':
            dt_fmt = '%Y-%m-%dT%H:%M:%S'
            try:
                _g['expired_dt'] = datetime.strptime(exp, dt_fmt)
            except:
                try:
                    _g['expired_dt'] = datetime.strptime(exp[:10], dt_fmt)
                except:
                    msg_exp = '(default)'
                    log.error(f"{fn} : Could not parse expiration timeframe. (set: 24hrs){msg_exp}")
                    _g['expired_dt'] = datetime.now()+timedelta(days=1)
        # -- from token
        else:
            ...  #ToDo:
        _g['expiry_type'] = kind

        log.info(f"{fn} : token expires on {datetime.strftime(_g['expired_dt'], dt_fmt)} {msg_exp}")
        return

    def use_basic_authen(self, b64=False, data_omits=None):
        self._auth_basic_type = True
        if b64:
            self._auth_basic_encoded = True
        if isinstance(data_omits, list):
            self._data_omits = data_omits

    def use_bearer(self):
        self._bearer = True
