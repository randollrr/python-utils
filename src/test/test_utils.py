import pytest
from auto_utils import Email


@pytest.fixture
def setup():
    ec = Email()
    yield {'ec': ec}

@pytest.mark.skip
def test_send_email():
    ec = setup['ec']
    ec.send_email("This a second test from the BARE Runner", "This a test of the BARE runner notification system")
