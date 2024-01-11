from datetime import datetime

import pytest
from common.utils import log, ts

import common.scheduler as sch


# @pytest.mark.skip('manual-run')
@pytest.mark.parametrize('req, ret', [
    ('', datetime.strptime(f"{ts(kind='date')}T12:12:59Z", '%Y-%m-%dT%H:%M:%SZ'))
])
def test_get_next_event(req, ret):
    res = sch.get_next_event(req)
    assert res == ret



def test_another_func(req, ret):
    res = ...
    assert res == ret

