import pytest
from utils import Email


@pytest.fixture
def setup():
    ec = Email()
    return {'ec': ec}


def test_send_email():
    ec = setup['ec']
    ec.send_email("This a second test from the BARE Runner", "This a test of the BARE runner notification system")
