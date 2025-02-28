import pytest

from common.utils import OAuth2


@pytest.fixture
def oauth():
    oauth2 = OAuth2()
    yield oauth2


@pytest.mark.parametrize('kind, exp, data, ret', [
    ('timelapse', 3600, None, False)
])
def test_handle_expiry(oauth, kind, exp, data, ret):
    if data:
        oauth.headers.Authorization = data
    oauth.handle_expiry(kind=kind, exp=exp)
    print(oauth)
    ...


@pytest.mark.parametrize('kind, exp, data, ret', [
    ('timelapse', 3600, None, False)
])
def test_expired(oauth, kind, exp, data, ret):
    if data:
        oauth.headers.Authorization = data
    res = oauth.expired()
    assert res == ret


def test_get_token(oauth):
    token = {
        'access_token': 'eyJhbGciOiJIUzI1NiJ9.xxx.xxx',
        'token_type': 'bearer',
        'expires_in': 3600
    }
    login_token = oauth._do_login()
    res = oauth.get_token(token)
    assert res == True
