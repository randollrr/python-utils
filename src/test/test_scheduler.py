from datetime import datetime

import pytest
from common.utils import log, ts, Status

import common.scheduler as sch


@pytest.mark.skip('manual-run')
@pytest.mark.parametrize('req, ret', [
    ('', datetime.strptime(f"{ts(kind='date')}T12:12:59Z", '%Y-%m-%dT%H:%M:%SZ'))
])
def test_get_next_event(req, ret):
    res = sch.get_next_event(req)
    assert res == ret


@pytest.mark.parametrize('job, params, ret', [
    ('cron.job_example', {'--say': 'hello world'}, Status(200, 'job_example ran successfully.'))
])
def test_run_job(job, params, ret):
    res = sch.run_job(job, params)
    assert res.code == ret.code

