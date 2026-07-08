from datetime import datetime

import pytest
from common.utils import log, ts, Status

import common.scheduler as sch


def test_get_list():
    res = sch._config_get_list()
    assert res is not None


def test_get_list():
    print(sch._config_get_list())
    assert True


def test_get_module():
    res = sch.get_module('cron.job_example')
    assert res is not None


@pytest.mark.skip('manual-run')
@pytest.mark.parametrize('req, ret', [
    ('', datetime.strptime(f"{ts(kind='date')}T12:12:59Z", '%Y-%m-%dT%H:%M:%SZ'))
])
def test_get_next_event(req, ret):
    res = sch.get_next_event(req)
    assert res == ret


def test_get_next_event_2():
    print(f"\n{sch.get_next_event('* * * * *')}")
    print(f"\n{sch.get_next_event('8 * * * *')}")
    print(f"\n{sch.get_next_event('0 0/12 * * *')}")
    print()
    for t in sch.get_next_event('0 4,16 * * *', 4):
        print(t)
    assert True


def test_isexecutable():
    res = sch.isexecutable(sch.get_next_event('* * * * *'))
    print(res)
    assert True


@pytest.mark.skip('manual-run')
def test_run_job_1():
    sch.run_job('ep_alerts.pa_job')
    assert True


@pytest.mark.parametrize('job, params, ret', [
    # (None, None, 200),
    ('cron.job_example', {'cron.job_example':{'say': 'hello world'}}, 200),
])
def test_run_job_2(job, params, ret):
    res = sch.run_job(job, params)
    assert res[0].code == ret


@pytest.mark.skip('manual-run')
def test_wakeup():
    print(sch.wakeup())
    assert True
