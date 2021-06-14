import pytest

from auto_fm import FileManager
from auto_utils import log, wd


@pytest.fixture
def _g():
    fm = FileManager()
    yield {
        'fm': fm,
        'pwd': 'dirstruct'
    }


def test_dir_struct(_g):
    fm = _g['fm']
    pwd = _g['pwd']

    # -- default path and directories
    fm.dir_struct()
    dir_list = [x[1] for x in fm.ls(f"{wd()}/fm")]
    assert  dir_list == ['archive', 'errored', 'input', 'output']

    # -- path provided
    fm.dir_struct(pwd, ['test1', 'test2', 'test3'])
    dir_list = [x[1] for x in fm.ls(pwd)]
    assert sorted(dir_list) == ['test1', 'test2', 'test3']


def test_touch(_g):
    fm = _g['fm']
    pwd = _g['pwd']

    fm.touch(f"{pwd}/test1/result.1")
    fm.touch(f"{pwd}/test1/result.2")
    fm.touch(f"{pwd}/test1/result.3")
    fm.touch(f"{pwd}/test1/result.4")
    files_list = [x[1] for x in fm.ls(f"{pwd}/test1")]
    assert files_list == ['result.1', 'result.2', 'result.3', 'result.4']


def test_exists(_g):
    fm = _g['fm']
    pwd = _g['pwd']

    assert fm.exists(f"{pwd}/test1/result.1")
    assert fm.exists(f"{pwd}/test2")
    assert not fm.exists(f"{'pwd'}/testx")


def test_list(_g):
    fm = _g['fm']
    pwd = _g['pwd']

    res = fm.ls(f"{pwd}/test1")
    assert  len(res) == 4

    res = fm.ls(f"{pwd}/test1", fn_only=True)
    assert  res == ['result.1', 'result.2', 'result.3', 'result.4']


def test_latest(_g):
    fm = _g['fm']
    pwd = _g['pwd']

    res = fm.latest(f"{pwd}/test1")
    assert  len(res) == 2

    res = fm.latest(f"{pwd}/test1", fn_only=True)
    assert  res == 'result.4'


def test_oldest(_g):
    fm = _g['fm']
    pwd = _g['pwd']

    res = fm.oldest(f"{pwd}/test1")
    assert  len(res) == 2

    res = fm.oldest(f"{pwd}/test1", fn_only=True)
    assert  res == 'result.1'


def test_retention(_g):
    fm = _g['fm']
    pwd = _g['pwd']

    fm.retainer(f"{pwd}/test1", 'result', 2)
    files_list = fm.ls(f"{pwd}/test1", fn_only=True)
    assert files_list == ['result.3', 'result.4']


def test_move(_g):
    fm = _g['fm']
    pwd = _g['pwd']

    res = fm.move('result.3', f"{pwd}/test1", f"{pwd}/test2")
    assert res

    files_list = fm.ls(f"{pwd}/test2", fn_only=True)
    assert 'result.3' in files_list


def test_del_files(_g):
    fm = _g['fm']
    pwd = _g['pwd']

    files_list = fm.ls(f"{pwd}/test2", fn_only=True)
    assert fm.del_files(f"{pwd}/test2", ['result.3'])
    assert not fm.del_files(['notfound'], f"{pwd}/test2")


def test_del_dir(_g):
    fm = _g['fm']
    pwd = _g['pwd']

    assert not fm.del_dir(f"{pwd}/test1")
    assert fm.del_files(f"{pwd}/test1", fn_pattern='result.*')
    assert fm.del_dir(f"{pwd}/test3")
    assert fm.del_dir(f"{pwd}/test2")
    assert fm.del_dir(f"{pwd}/test1")
    log.debug(fm.ls(pwd))
    assert fm.del_dir(f"{pwd}")
