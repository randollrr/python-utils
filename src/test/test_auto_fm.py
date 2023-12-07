import pytest

from auto_fm import FileManager
from auto_utils import log, wd

_g = {'pwd': f'{wd()}/dirstruct'}


@pytest.fixture
def fm():
    """
    setup a structured directory for testing.
    """
    # -- setup
    fm = FileManager()
    yield fm

    # -- teardown
    remove_everything(fm)

# ToDo:
# fm.cd() is not working well, add _update_paths() [port from dir_struct()]
# ensure certain function cannot afftect filesystem above fm/:
# - del_*(), mkdirs(), cd()
# remove status as default from fm.fullpath()


def remove_everything(fm):
    files = fm.ls(ret='dict')
    print(files)
    for f in files:
        if f['is_dir']:
            ...
    # fm.reset()


def test_cd(fm):
    # fm.dir_struct(_g['pwd'])
    fm.dir_struct()
    root = fm.ls()
    res = fm.cd('input')
    print(fm.ls())
    assert res.code == 200


@pytest.mark.parametrize('path, ff, ret', [
    # ('', '', 200),
    # (None, None, 204),
    # ('' ,'json', 200),
    # ('', 'dict', 200),
    (wd(), 'list', 200),
])
def test_crawl_dir(fm, path, ff, ret):
    res, status = fm.crawl_dir(path=path, ret=ff)
    assert res
    assert status.code == ret


def test_del_files(fm):
    fm.dir_struct(_g['pwd'])

    files_list = fm.ls(f"{_g['pwd']}/fm/test2", fn_only=True)
    assert fm.del_files(f"{_g['pwd']}/fm/test2", ['result.3'])
    assert not fm.del_files(['notfound'], f"{_g['pwd']}/fm/test2")


def test_del_dir(fm):
    fm.dir_struct(_g['pwd'], ['test1', 'test2', 'test3'])
    fm.touch('test1/result.1')
    log.debug(fm.ls('test1', ret='json'))

    assert not fm.del_dir(f"./test1")
    assert fm.del_files(f"./test1", fn_pattern='result.*')
    assert fm.del_dir(f"./test3")
    assert fm.del_dir(f"./test2")
    assert fm.del_dir(f"./test1")
    log.debug(fm.ls(ret='json'))
    assert fm.del_dir(f".")


def test_dir_struct(fm):
    fm.dir_struct(_g['pwd']) # -- default path and directories

    # dir_list = [x[1] for x in fm.ls(f"./fm")]
    # dirs = fm.ls(fm.pwd())
    dirs = fm.ls()
    dir_list = [x[1] for x in dirs]
    assert  dir_list == ['archive', 'errored', 'input', 'output']

    assert fm.del_dir(fm.ARCHIVE)
    assert fm.del_dir(fm.ERRORED)
    assert fm.del_dir(fm.INPUT)
    assert fm.del_dir(fm.OUTPUT)
    assert fm.del_dir(_g['pwd'])

    # -- path provided
    fm.dir_struct(_g['pwd'], ['test1', 'test2', 'test3'])
    dir_list = [x[1] for x in fm.ls(f"{_g['pwd']}/fm")]
    assert sorted(dir_list) == ['test1', 'test2', 'test3']

    assert fm.del_dir(f"{fm.pwd()}/test1")
    assert fm.del_dir(f"{fm.pwd()}/test2")
    assert fm.del_dir(f"{fm.pwd()}/test3")
    assert fm.del_dir(_g['pwd'])


def test_dirstruct_bucket():
    fm.dir_struct(_g['pwd'])

    fm.set_bucket('39c65e13bcb0')

    fm.touch(f"{fm.INPUT}/result.txt")
    res = fm.ls(f"{_g['pwd']}/fm/input/39c65e13bcb0", fn_only=True)
    log.debug(fm.ls(fm.INPUT, fn_only=True))
    log.debug(res)
    assert res  == ['result.txt']
    assert fm.del_files(f"{fm.INPUT}", ['result.txt'])
    # assert fm.del_dir(fm.INPUT)
    # assert fm.del_dir(fm.OUTPUT)
    # assert fm.del_dir(fm.ARCHIVE)
    # assert fm.del_dir(fm.ERRORED)
    res = fm.del_dir(_g['pwd'])
    assert res


def test_exists(fm):
    fm.dir_struct(_g['pwd'], ['test1', 'test2'])
    fm.touch('test1/result.1')

    assert fm.exists(f"{_g['pwd']}/fm/test1/result.1")
    assert fm.exists(f"{_g['pwd']}/fm/test2")
    assert not fm.exists(f"{'pwd'}/fm/testx")


@pytest.mark.parametrize('req, ret', [
    (None, None),
    ('', ''),
    ('/workspace/python-utils/src/app', '/workspace/python-utils/src/app'),
    ('.', '/workspace/python-utils/src/app'),
    ('.archive', '/workspace/python-utils/src/app/.archive'),
    ('./', '/workspace/python-utils/src/app/'),
    ('./fm', '/workspace/python-utils/src/app/fm'),
    ('fm/input', '/workspace/python-utils/src/app/fm/input'),
    ('/workspace/python-utils/src/app/.', '/workspace/python-utils/src/app'),
    ('/workspace/python-utils/src/app/', '/workspace/python-utils/src/app/'),
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
def test_fullpath(fm, req, ret):
    mockdata = '/workspace/python-utils/src/app'
    res, _ = fm.fullpath(req, status=True, di=mockdata)
    res = fm.fullpath(req, di=mockdata)
    assert res == ret


def test_latest(fm):
    fm.dir_struct(_g['pwd'])

    res = fm.latest(f"{_g['pwd']}/fm/test1")
    assert  len(res) == 2

    res = fm.latest(f"{_g['pwd']}/fm/test1", fn_only=True)
    assert  res == 'result.4'


def test_list(fm):
    fm.dir_struct(_g['pwd'])

    res = fm.ls(f"{_g['pwd']}/fm/test1")
    assert  len(res) == 4

    res = fm.ls(f"{_g['pwd']}/fm/test1", fn_only=True)
    assert  res == ['result.1', 'result.2', 'result.3', 'result.4']


@pytest.mark.parametrize('req', [(f"{_g['pwd']}/fm")])
def test_ls_list(req):
    fm.dir_struct(_g['pwd'])
    res = fm.ls(req)
    for f in res:
        assert isinstance(f[0], int)
        assert isinstance(f[1], str)

    remove_everything(_g['pwd'])


@pytest.mark.parametrize('req', [
    ('dict'),
    ('json')
])
def test_ls_object(req):
    fm.dir_struct(_g['pwd'])
    res = fm.ls(ret=req)
    print(res)
    assert res


@pytest.mark.parametrize('req, ret', [
    (f"{_g['pwd']}/fm", ['archive', 'errored', 'input', 'output'])
])
def test_ls_fn_only(req, ret):
    res = fm.ls(req, fn_only=True)
    assert res == ret


@pytest.mark.parametrize('req, ret', [
    ('sub1/sub2/sub3', f"{_g['pwd']}/fm/archive/abcdef/sub1/sub2/sub3")
])
def test_mkdirs(fm, req, ret):
    fm.dir_struct(_g['pwd'])
    fm.set_bucket('abcdef')
    res = fm.mkdirs(f"{fm.ARCHIVE}/{req}")
    assert res.code == 200
    assert fm.exists(ret)


def test_move(fm):
    fm.dir_struct(_g['pwd'])
    res = fm.move('result.3',
                  f"{_g['pwd']}/fm/test1",
                  f"{_g['pwd']}/fm/test2")
    assert res

    files_list = fm.ls(f"{_g['pwd']}/fm/test2", fn_only=True)
    assert 'result.3' in files_list


def test_oldest(fm):
    fm.dir_struct(_g['pwd'])

    res = fm.oldest(f"{_g['pwd']}/fm/test1")
    assert  len(res) == 2

    res = fm.oldest(f"{_g['pwd']}/fm/test1", fn_only=True)
    assert  res == 'result.1'


def test_retention(fm):
    fm.dir_struct(_g['pwd'])

    fm.retainer(f"{_g['pwd']}/fm/test1", 'result', 2)
    files_list = fm.ls(f"{_g['pwd']}/fm/test1", fn_only=True)
    assert files_list == ['result.3', 'result.4']


def test_touch(fm):
    fm.dir_struct(_g['pwd'])

    log.debug(f"{fm._bucket}")

    fm.touch(f"{_g['pwd']}/fm/test1/result.1")
    fm.touch(f"{_g['pwd']}/fm/test1/result.2")
    fm.touch(f"{_g['pwd']}/fm/test1/result.3")
    fm.touch(f"{_g['pwd']}/fm/test1/result.4")
    files_list = [x[1] for x in fm.ls(f"{_g['pwd']}/fm/test1")]
    assert files_list == ['result.1', 'result.2', 'result.3', 'result.4']
