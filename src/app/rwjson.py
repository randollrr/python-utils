import json


_g = {}


def _rwjson(action, fn):
    if action == 'read':
        try:
            _g.setdefault(fn, None)
            with open(f"{wd()}/_{fn}.json", 'r') as f:
                _g[f'{fn}'] = json.load(f)
        except:
            pass
    if action == 'write':
        with open(f"{wd()}/_{fn}.json", 'w') as f:
            json.dump(_g[f'{fn}'], f)

