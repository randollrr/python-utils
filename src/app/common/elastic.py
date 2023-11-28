from datetime import datetime, timedelta

from common.utils import config, log, Status
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search


class ElasticConnection:
    def __init__(self) -> None:
        self.client = None
        self.timeout = 120
        if config['elastic']:
            self.host = config['elastic']['url']
            self.client = Elasticsearch(
                hosts=[f'https://{self.host}:9243'],
                http_auth=(config['elastic']['username'], config['elastic']['password']),
                ssl_show_warn=False,
                request_timeout=self.timeout, max_retries=10, retry_on_timeout=True)
            # log.debug(self.client.cluster.health(request_timeout=self.timeout))


class ElasticCRUD(ElasticConnection):
    def __init__(self, index=None) -> None:
        super().__init__()
        self.index = None
        if config['elastic']:
            self.index = config['elastic']['index'] if not index else index
        self.s = Search(using=self.client)

    def create(self):
        ...

    def read(self, where=None, collection=None, db=None, projection=None,
        sort=None, agg=None, select=None, table=None, groupby=None, like=None,
        query=None, index=None, limit=None, offset=None, interval=None,
        metadata=False) -> dict:
        r = []
        s = Status(404, 'No data found.')
        _s_type = 'match'

        # -- build parameters
        q = {}
        if query is None:
            if where:
                # q[_s_type] = where
                q = where
        if isinstance(query, dict):
            for k, v in query.items():
                # q[_s_type].update({k: v})
                q.update({k: v})
        if index:
            self.index = index
        else:
            if collection:
                self.index = index = collection
            elif table:
                self.index = index = table
            elif db:
                self.index = index = db
            else:
                index = self.index
        if interval is None:
            interval = {'hour': 1}

        # -- fetch data
        log.debug(f"Sending request: {q}")
        self.s.query(_s_type, **q)
        self.s.filter('range', **ts_range(interval=interval))
        # data = self.s.index(index).execute()
        data = self.s.index(index).scan()
        s.table = index
        s.kind = _s_type
        # s.docs = self.s.count()
        # s.hits = r.hits.total.to_dict()

        # -- build r(esult) object
        for hit in data:
            d = hit.to_dict()
            if metadata:
                d.setdefault('_meta', {})
                for item in hit.meta:
                    k, v = (item, str(hit.meta[item])) if item == 'sort' else (item, hit.meta[item])
                    d['_meta'].update({k: v})
            r += [d]
        del data

        return self._response(r, s)

    def update(self):
        ...

    def delete(self):
        ...

    def set_index(self, idx):
        self.index = idx

    def _response(self, data, status) -> dict:
        r = {'status': {'code': None, 'message': None}, 'data': []}

        if data:
            r['data'] = data; del data
            status.code = 200
            status.message = 'OK'
            status.docs = len(r['data'])
            r['status'] = status.to_dict()

        return r


def ts_range(start_dt=None, end_dt=None, interval=None, ts_field=None, indexes=None) -> dict:
    """
    see: https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-date-format.html
    """
    r = {}
    gte = None
    lte = datetime.utcnow() if end_dt is None else end_dt

    def cint(_v):
        try:
            return int(_v)
        except:
            return 0

    def fmt_dt(_dt: datetime):
        return datetime.strftime(_dt, '%Y-%m-%dT%H:%M:%SZ') if isinstance(_dt, datetime) else None

    if interval:
        # if isinstance(interval, int):
        #     ...
        # elif isinstance(interval, str) and 'now' in interval:
        #     ...
        if isinstance(interval, dict):
            k, v, t = '', 0, 0
            if len(interval.items()) > 0:
                k, v = tuple(interval.items())[0]
            v = cint(v)
            if k == 'sec' or k == 'second' or k == 'seconds':
                t = v
            if k == 'min' or k == 'minute' or k == 'minutes':
                t = v*60
            if k == 'hr' or k == 'hrs' or k == 'hour' or k == 'hours':
                t = v*60*60
            if k == 'day' or k == 'days':
                t = v*24*60*60
            elif k == 'week' or k == 'weeks':
                t = v*7*24*60*60
            elif k == 'month' or k == 'months':
                t = v*30*24*60*60
            elif k == 'year' or k == 'years':
                t = v*365*24*60*60
            gte = lte - timedelta(seconds=t)

        field = '@timestamp' if ts_field is None else ts_field
        r = {
            field: {
                'gte': fmt_dt(gte),
                'lte': fmt_dt(lte),
                'format': 'strict_date_optional_time'
            }
        }

    return r


dao = ElasticCRUD()


# CHANGELOG

# ### v1.0.0 auto_elastic
# d- implement read() using default index
# d- allow easy change of index on read()
# d- show _meta object in every doc (hide: default)
# - add limit param (default: 1000)
# - add agg type: count
# - aggregate on selected fields
