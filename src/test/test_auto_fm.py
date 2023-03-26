import pytest

from auto_fm import FileManager
from auto_utils import log


@pytest.fixture
def _g():
    yield {
        'fm': FileManager(),
        'pwd': 'dirstruct'
    }


def test_dir_struct(_g):
    fm = _g['fm']
    pwd = _g['pwd']
    fm.dir_struct(pwd) # -- default path and directories

    # dir_list = [x[1] for x in fm.ls(f"./fm")]
    dirs = fm.ls(fm.basedir)
    dir_list = [x[1] for x in dirs]
    assert  dir_list == ['archive', 'errored', 'input', 'output']
    assert fm.del_dir(fm.ARCHIVE)
    assert fm.del_dir(fm.ERRORED)
    assert fm.del_dir(fm.INPUT)
    assert fm.del_dir(fm.OUTPUT)
    assert fm.del_dir(pwd)

    # -- path provided
    fm.dir_struct(pwd, ['test1', 'test2', 'test3'])
    dir_list = [x[1] for x in fm.ls(f"{pwd}/fm")]
    assert sorted(dir_list) == ['test1', 'test2', 'test3']
    assert fm.del_dir(f"{fm.pwd()}/test1")
    assert fm.del_dir(f"{fm.pwd()}/test2")
    assert fm.del_dir(f"{fm.pwd()}/test3")
    assert fm.del_dir(pwd)


def test_touch(_g):
    fm = _g['fm']
    pwd = _g['pwd']
    fm.dir_struct(pwd)

    log.debug(f"{fm.bucket}")

    fm.touch(f"{pwd}/fm/test1/result.1")
    fm.touch(f"{pwd}/fm/test1/result.2")
    fm.touch(f"{pwd}/fm/test1/result.3")
    fm.touch(f"{pwd}/fm/test1/result.4")
    files_list = [x[1] for x in fm.ls(f"{pwd}/fm/test1")]
    assert files_list == ['result.1', 'result.2', 'result.3', 'result.4']


def test_exists(_g):
    fm = _g['fm']
    pwd = _g['pwd']
    fm.dir_struct(pwd)

    assert fm.exists(f"{pwd}/fm/test1/result.1")
    assert fm.exists(f"{pwd}/fm/test2")
    assert not fm.exists(f"{'pwd'}/fm/testx")


def test_list(_g):
    fm = _g['fm']
    pwd = _g['pwd']
    fm.dir_struct(pwd)

    res = fm.ls(f"{pwd}/fm/test1")
    assert  len(res) == 4

    res = fm.ls(f"{pwd}/fm/test1", fn_only=True)
    assert  res == ['result.1', 'result.2', 'result.3', 'result.4']


def test_latest(_g):
    fm = _g['fm']
    pwd = _g['pwd']
    fm.dir_struct(pwd)

    res = fm.latest(f"{pwd}/fm/test1")
    assert  len(res) == 2

    res = fm.latest(f"{pwd}/fm/test1", fn_only=True)
    assert  res == 'result.4'


def test_oldest(_g):
    fm = _g['fm']
    pwd = _g['pwd']
    fm.dir_struct(pwd)

    res = fm.oldest(f"{pwd}/fm/test1")
    assert  len(res) == 2

    res = fm.oldest(f"{pwd}/fm/test1", fn_only=True)
    assert  res == 'result.1'


def test_retention(_g):
    fm = _g['fm']
    pwd = _g['pwd']
    fm.dir_struct(pwd)

    fm.retainer(f"{pwd}/fm/test1", 'result', 2)
    files_list = fm.ls(f"{pwd}/fm/test1", fn_only=True)
    assert files_list == ['result.3', 'result.4']


def test_move(_g):
    fm = _g['fm']
    pwd = _g['pwd']
    fm.dir_struct(pwd)

    res = fm.move('result.3', f"{pwd}/fm/test1", f"{pwd}/fm/test2")
    assert res

    files_list = fm.ls(f"{pwd}/fm/test2", fn_only=True)
    assert 'result.3' in files_list


def test_del_files(_g):
    fm = _g['fm']
    pwd = _g['pwd']
    fm.dir_struct(pwd)

    files_list = fm.ls(f"{pwd}/fm/test2", fn_only=True)
    assert fm.del_files(f"{pwd}/fm/test2", ['result.3'])
    assert not fm.del_files(['notfound'], f"{pwd}/fm/test2")


def test_del_dir(_g):
    fm = _g['fm']
    pwd = _g['pwd']
    fm.dir_struct(pwd)

    assert not fm.del_dir(f"{pwd}/fm/test1")
    assert fm.del_files(f"{pwd}/fm/test1", fn_pattern='result.*')
    assert fm.del_dir(f"{pwd}/fm/test3")
    assert fm.del_dir(f"{pwd}/fm/test2")
    assert fm.del_dir(f"{pwd}/fm/test1")
    log.debug(fm.ls(pwd))
    assert fm.del_dir(f"{pwd}/fm")
    assert fm.del_dir(f"{pwd}")


def test_dirstruct_bucket(_g):
    fm = _g['fm']
    pwd = _g['pwd']
    fm.dir_struct(pwd)

    fm.setbucket('39c65e13bcb0')

    fm.touch(f"{fm.INPUT}/result.txt")
    res = fm.ls(f"{pwd}/fm/input/39c65e13bcb0", fn_only=True)
    log.debug(fm.ls(fm.INPUT, fn_only=True))
    log.debug(res)
    assert res  == ['result.txt']
    assert fm.del_files(f"{fm.INPUT}", ['result.txt'])
    # assert fm.del_dir(fm.INPUT)
    # assert fm.del_dir(fm.OUTPUT)
    # assert fm.del_dir(fm.ARCHIVE)
    # assert fm.del_dir(fm.ERRORED)
    res = fm.del_dir(pwd)
    assert res


@pytest.mark.parametrize('req, ret', [
    ('', ''),
    (None, None),
    ('.', '/workspace/python-utils/src/app'),
    ('/workspace/python-utils/src/app/.', '/workspace/python-utils/src/app'),
    ('./', '/workspace/python-utils/src/app/'),
    ('/workspace/python-utils/src/app/', '/workspace/python-utils/src/app/'),
    ('./fm', '/workspace/python-utils/src/app/fm'),
    ('..', '/workspace/python-utils/src'),
    ('../', '/workspace/python-utils/src/'),
    ('../..', '/workspace/python-utils'),
    ('../../', '/workspace/python-utils/'),
    ('../../..', '/workspace'),
    ('../../../..', '/'),
    ('../../../../', '/'),
    ('../../../../../../../../../../../..', '/'),
    ('/workspace/python-utils/src/app/../test', '/workspace/python-utils/src/test'),
    ('/workspace/python-utils/src/app/../../.git', '/workspace/python-utils/.git'),
    ('/workspace/python-utils/src/app/../../.git/hooks/../logs', '/workspace/python-utils/.git/logs'),
])
def test_fullpath(_g, req, ret):
    mockdata = '/workspace/python-utils/src/app'
    res, _ = _g['fm'].fullpath(req, di=mockdata)
    assert res == ret
