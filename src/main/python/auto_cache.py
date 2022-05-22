import json
import time

from auto_mongo import dao
from auto_utils import log

__version__ = '1.0.2'
_caching = {}


class Cache:
    """
    Save/load all data in global "_caching" object to file system.
    """
    # FS = 'fs'
    # DB = 'mongo'

    def __init__(self, fn=None, ttl=None, backend=None, schema=None) -> None:

        if not fn:
            self.fn = 'caching.json'
        self.lastupdated = self._ts()
        self.ttl = 600 if not ttl else ttl
        self.backend = 'fs' if not backend else backend
        self.schema = 'app_caching' if not schema else schema
        self._load()

    def add(self, k, v):
        _caching[k] = {'data': v, 'lastupdated': self._ts()}
        self._save()

    def get(self, k):
        return _caching.get(k)

    def getall(self):
        return _caching

    def _load(self):
        if self.backend == 'fs':
            try:
                with open(self.fn, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        for d in data:
                            _caching[d] = data[d]
            except:
                pass
        elif self.backend == 'mongo':
            data = dao.read1({}, self.schema)
            for d in data:
                _caching[d] = data[d]

    def ok(self, k:str=None) -> bool:
        def notexpired(_c_obj: dict) -> bool:
            if _c_obj and isinstance(_c_obj, dict) and \
                _c_obj.get('lastupdated') and \
                    self._ts() <= (int(_c_obj.get('lastupdated'))+self.ttl):
                    return True
            else:
                _c_obj = {}
                self._save()
                return False

        # -- expired timestamp check
        if k:
            return notexpired(_caching.get(k))
        else:
            ret_list = []
            for k in _caching.keys():
                if k != '_id':
                    ret_list += [notexpired(_caching.get(k))]
            return all(ret_list)

    def reset(self, k=None):
        if k == 'lastupdated':
            self.lastupdated = self._ts()
        if isinstance(_caching, dict) and not k:
            for d in _caching:
                _caching[d] = {}
        elif _caching.get(k):
            _caching[k] = {}
        self._save()

    def _save(self, k=None):
        if self.backend == 'fs':
            with open(self.fn, 'w') as f:
                json.dump(_caching, f)
        elif self.backend == 'mongo':
            if k:
                data = dao.read1({k: {'exists': True}}, self.schema)
            else:
                data = dao.read1({}, self.schema)
            if data:
                dao.update(_caching, self.schema)
            else:
                dao.create(_caching, self.schema)

    def _ts(self):
        return int(time.time())


cache = Cache()


# -- History

# 1.0.0  initial implementation
# 1.0.1  add support to different backend i.e. mongo
# 1.0.2  optimize ok() function
