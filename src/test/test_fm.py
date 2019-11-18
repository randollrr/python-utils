import pytest
from auto_fm import FileManager


@pytest.fixture
def setup():
    fm = FileManager()
    yield {'fm': fm}


def test_dir_struct(setup):
    fm = setup['fm']
    assert fm.dir_struct('tmp', ['test1', 'test2', 'test3'])


def test_retention(setup):
    fm = setup['fm']
    fm.touch('{}/result.1'.format('tmp/test1'))
    fm.touch('{}/result.2'.format('tmp/test1'))
    fm.touch('{}/result.3'.format('tmp/test1'))
    fm.touch('{}/result.4'.format('tmp/test1'))
    fm.retainer('tmp/test1', 'result', 2)
