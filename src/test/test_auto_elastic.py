import json
import pytest

from auto_elastic import ElasticCRUD, ts_range
from connectors import device_querier as dq

@pytest.mark.parametrize('inp, out', [
    (15, True),
    ({'hour': 1}, True),
    ({'hour': 2}, True),
    ({'day': 1}, True),
    ({'days': 7}, True),
    ({'month': 1}, True),
    ({'months': 6}, True),
    ({'year': 1}, True),
])
def test_ts_range(inp, out):
    out = ts_range(interval=inp)
    print()
    print(inp)
    print(out)
    assert inp and out



@pytest.mark.parametrize('inp, out, idx', [
    # ({'a_node': '*'}, 1, 'latest-*'),
    ({'a_node':'blvuslrc01'}, 1, 'latest-*'),
    # ({'sys_message': '(*ROUTING-BGP-5-ADJCHANGE_DETAIL* and (Down or Up)) or '
    #                   '(*RPD_BGP_NEIGHBOR_STATE_CHANGED* and (Idle or Established)) '
    #                   'or (*bgp_recv*)'}, 1, 'backbone_logs-*'),
    # ({'site': 'ashb'}, 1, 'telemetry-*'),
])
def test_read_index_multiple(inp, out, idx):
    dao = ElasticCRUD()
    res = dao.read(inp, table=idx, metadata=True)
    # print(res)
    # print(json.dumps(res, indent=4))
    for d in res['data']:
        if d.get('a_node'):
            print(d['a_node'])
        elif d.get('host'):
            print(d['host'])
        else:
            print('...')
    assert len(res) > out


@pytest.mark.parametrize('i, o', [
    ({'a_node': '*'}, 1),
    ({'a_node': 'blvuslrc01'}, 1),
    (None, 1),
    ({}, 1),
])
def test_read_index_latest(i, o):
    dao = ElasticCRUD()
    res = dao.read(i, metadata=True, limit=100)
    print(json.dumps(res, indent=4))
    assert len(res) > o
