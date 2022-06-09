
import pytest
from auto_utils import config, envar_in, Email, log


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
    ('APP_RUNTIME_NAME', 'APP_RUNTIME_NAME'),
    ('((env:APP_RUNTIME_NAME))', 'app'),
    ('/usr/bin/((env:APP_RUNTIME_NAME)).sh', '/usr/bin/app.sh'),
])
def test_envar_in(i, o):
    assert envar_in(i) == o


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
