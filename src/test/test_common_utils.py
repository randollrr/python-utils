from datetime import datetime, timezone

import pytest
from common.utils import config, envar, envar_in, Email, log, Status, next_add, \
    ts


def test_config_file_type():
    assert config.file_type() == 'json'


@pytest.mark.parametrize('i, o',[
    ('keys', 'a1b2c3-d4e5f6-g7h8k9-l0m1n2'),
    # ('secret', 'hdDrA1D#me2fr!3$hW'),
    ('user', 'itsme@email.com')
])
def test_config_get(i, o):
    assert config['external-api'][i] == o


@pytest.mark.parametrize('i, o', [
    (None, None),
    (8, 8),
    ('APP_NAME', 'APP_NAME'),
    ('((env:APP_NAME))', 'app'),
    ('/usr/bin/((env:APP_NAME)).sh', '/usr/bin/app.sh'),
    ('this is the path: "((env:PYTHONPATH))", we were talking about',
     'this is the path: "./src/app:./src/test", we were talking about')
])
def test_envar_in(i, o):
    assert envar_in(i) == o


@pytest.mark.parametrize('req, ret', [
    ('', None),
    (None, None),
    ('PYTHONPATH', './src/app:./src/test'),
    ('GCP', None),
])
def test_envar(req, ret):
    res = envar(req)
    assert res == ret


# def test_send_mail():
#     em = Email({"message": {
#         "from": "me@email.com",
#         "to": "you@email.com",
#         "reply-to": None,
#         "server": "smtp.gmail.com",
#         "port": 587,
#         "username": None,
#         "password": None,
#         "tls-required": True,
#         "plain-passwd": True
#     }})

#     # em = Email()
#     res = em.send_mail({
#         'from': 'me@email.com',
#         'to': 'you@email.com',
#         'subject': 'this is a test...',
#         'body': "I didn't really have much to write :-)."})
#     assert res

#     server.send_email(
#         "This a second test from the Component Runner",
#         "This a test of the BARE runner notification system",
#         from_addr='',
#         to_addr='')
#     assert True


def test_status():
    status = Status(404, 'No data found.')
    print(status)
    status.code = 200
    status.message = 'OK'
    status.docs = 31
    assert isinstance(status, Status)
    assert isinstance(str(status), str)
    assert isinstance(status.to_str(), str)
    assert isinstance(status.to_dict(), dict) and len(status.to_dict()) == 3
    print(status)


@pytest.mark.parametrize('text, ret', [
    (None, None),
    ('abc0', 'abc1'),
    ('randoll-123', 'randoll-124'),
    ('23423abc', '23423abc'),
    ('abc12xyz03', 'abc12xyz04'),
])
def test_route_next_add(text, ret):
    res = next_add(text)
    assert res == ret

def test_ts():
    dt_dt = '2024-01-31T23:59:59Z'
    dt_obj = datetime(2024, 1, 31, 23, 59, 59).astimezone(timezone.utc)
    dt_ts = dt_obj.timestamp()

    assert ts('date', from_dt=dt_dt) == '2024-01-31'
    assert ts('object', from_obj=dt_obj) == dt_obj
    assert ts('object', from_ts=dt_ts) == datetime.fromtimestamp(dt_ts, timezone.utc)
    assert ts(from_obj=dt_obj) == '2024-01-31T23:59:59Z'
    assert ts(from_dt=dt_dt) == '2024-01-31T23:59:59Z'

    assert ts()
    # assert ts('date') == '2025-02-28'
    assert ts('object', from_dt='2024-01-31T23:59:59') == None
    assert ts(from_ts=1234567890)
    assert ts(from_obj=datetime.now(timezone.utc))
