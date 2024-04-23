from datetime import datetime

import pytest
from common.utils import log, ts, Status

import common.scheduler as sch


def test_get_list():
    res = sch.get_list()
    assert res is not None


def test_get_mod():
    res = sch.get_mod('cron.job_example')
    assert res is not None


@pytest.mark.skip('manual-run')
@pytest.mark.parametrize('req, ret', [
    ('', datetime.strptime(f"{ts(kind='date')}T12:12:59Z", '%Y-%m-%dT%H:%M:%SZ'))
])
def test_get_next_event(req, ret):
    res = sch.get_next_event(req)
    assert res == ret


@pytest.mark.parametrize('job, params, ret', [
    # (None, None, 200),
    ('cron.job_example', {'cron.job_example':{'say': 'hello world'}}, 200),
])
def test_run_job(job, params, ret):
    res = sch.run_job(job, params)
    assert res[0].code == ret
