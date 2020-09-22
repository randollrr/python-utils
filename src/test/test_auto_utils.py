from typing import Container
import pytest
from auto_utils import config, log

# _g = {
#     'ec': Email()
# }


def test_config_file_type():
    assert config.file_type() == 'json'

# @pytest.mark.skip()
# def test_send_email():
#     ec = _g['ec']
#     ec.send_email("This a second test from the Component Runner", "This a test of the BARE runner notification system")
