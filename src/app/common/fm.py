import json
import os
import re

from common.utils import deprecated, log, envar, Status, wd

__authors__ = ['randollrr']
__version__ = '2.5.0-dev.6'


class FileManager:
    """
    Utility (interface) to facilitate REST-based file-system management. Also
    implements methods to manipulate file(s) with common automation operations.
    """

    def __init__(self, indir=None, outdir=None, arcdir=None, errdir=None, \
        known_dir=None, bucket=None) -> None:
        self.reset(indir, outdir, arcdir, errdir, known_dir, bucket)

    def cd(self, newpath) -> Status:
        s = Status(204, 'Nothing happened')
        n, s_fp = self.fullpath(newpath, status=True)
        if s_fp.code == 200:
            self._basedir = n
            s.code = 200
            s.message = f"new directory: {n}"
        else:
            s.code = s_fp.code
            s.message = s_fp.message
        return s

    def crawl_dir(self, path=None, ret=None) -> tuple[list, Status]:
        r = set()
        s = Status(204, 'Nothing happened.')

        if not ret or ret == '':
            ret = 'list'
        if not path or path == '':
            path = self.pwd()
        if isinstance(path, str):
            path = self.fullpath(path)
            res = os.walk(path)
            if res:
                t = []
                s.code = 200
                s.message = 'OK'

                for p in res:
                    t += [{
                        'path': p[0],
                        'dirs': p[1],
                        'files': p[2],
                    }]
                if ret == 'list':
                    for i in t:
                        for d in i['dirs']:
                            _res, _ = self.crawl_dir(f"{i['path']}/{d}", ret)
                            _i = None
                            for _i in _res:
                                r.add(_i)
                            del _res, _i
                        for f in i['files']:
                            r.add(f"{i['path']}/{f}")
                    r = sorted(r)
                # elif ret == 'json':
                #     r = json.dumps(t, indent=4)
                else:
                    r = sorted(t, key=lambda x: x['path'])  # returns dict
                del t
        return r, s

    def del_dir(self, path):
        """
        Delete directory provided (as long as it's not a set bucket).
        :param path: directory (only)
        :return: True or False
        """
        r = False
        try:
            if self.pwd() == f"{path}/fm":
                os.rmdir(self.pwd())  # remove "/fm/" 1st before "dirstruct"
            if self._bucket and path.endswith(self._bucket):
                # os.rmdir(path)
                # path = path.replace(self._bucket, '')
                log.warn(f"fm.del_dir(): Cannot delete {self._bucket} in path provided. "
                            f"Use fm.del_bucket() instead.")
                return r
            os.rmdir(path)
            r = True
            log.info(f"removed dir: {path}")
        except Exception as e:
            log.error(f"Couldn't remove directory: {e}.")
        return r

    def del_files(self, path, files=None, dir_flag=False, fn_pattern=None):
        """
        Delete list of files provided.
        :param path: directory (only)
        :param files: list [] of files
        :param fn_pattern: override [files] if provided
        :return: True or False
        """
        r = False
        if self.exists(path):
            if fn_pattern:
                files = self.ls(path, fn_pattern=fn_pattern, fn_only=True)

            if files is None:
                path, files = '/'.join(path.split('/')[:-1]), path.split('/')[-1]

            if isinstance(files, str):
                files = [files]

            if isinstance(files, list):
                for fn in files:
                    try:
                        if fn == '.keep':
                            log.info(f"skipped: {path}/{fn}")
                        else:
                            os.remove(os.path.join(path, fn))
                            log.info(f"deleted: {path}/{fn}")
                        r = True
                    except Exception as e:
                        log.error(f"Couldn't remove file: {e}")
            else:
                log.debug('Expected a list of files or a path with flag "dir=True"')
        return r

    def dir_struct(self, path=None, known_dir=None, auto_create=True):
        """
        Check directory structure. If not valid, create structure.
        :param path: filesystem full path
        :param known_dir: list of dir paths
        :return: True or False
        """
        r = False

        def update_path(_p, _np):
            _np = _np[:-1] if _np.endswith('/') else _np

            if _p == 'archive':
                self.ARCHIVE = _np
            elif _p == 'errored':
                self.ERRORED = _np
            elif _p == 'input':
                self.INPUT = _np
            elif _p == 'output':
                self.OUTPUT = _np

        if not path:
            path = '.'
        path = self.fullpath(path)
        if path:
            if '/fm' not in path:
                self._basedir = f"{path}/fm"
            else:
                self._basedir = f"{path}"
        if not self.known_dir:
            self.known_dir = ['archive', 'errored', 'input', 'output']
        if known_dir:
            self.known_dir = known_dir

        log.info(f"validate directory structure for: {self._basedir}")
        try:
            # i = 0
            for d in self.known_dir:
                n_path = os.path.join(self._basedir, d, self._bucket)
                update_path(d, n_path)
                if not os.path.exists(n_path):
                    log.info(f"creating: {n_path}")
                    if auto_create:
                        os.makedirs(n_path)
                    else:
                        log.info(f"  auto_create is off, did not create: {n_path}")
                        return r
                else:
                    log.info(f"already exists: {n_path}")
            r = True
        except Exception as e:
            log.error(f"Couldn't setup directory structure.\n{e}")
        return r

    def exists(self, path=None) -> bool:
        r = False
        if isinstance(path, str) and os.path.exists(path):
            r = True
        return r

    def find(self, fn_pattern, path=None, ret='list') -> list:
        """
        Find file(s) based on filename.
        :param filename: filename pattern
        :param path: directory to scan
        :param ret: change type of return values to receive (default: list)
        :return: list of [filename, timestamp], list of [<dict>] or list of [<json>]
        """
        fn = '[common.fm][find]'
        r = []
        t = {}

        log.info(f'finding for: "{fn_pattern}" in {path}')

        if not fn_pattern:
            fn_pattern = '.*'
        try:
            regex = re.compile(fn_pattern)
        except Exception as e:
            log.error(f"{fn} : Error: {e}")
            regex = None

        if regex:
            res = self.walk(path, ret='object')
            p, f = None, None
            for p in res:
                for f in p['files']:
                    if re.match(fn_pattern, f):
                        t.setdefault(p['path'], {'files': []})
                        t[p['path']]['files'] += [f]
            del res, p, f
            if ret == 'list':
                p, items = None, None
                for p, items in t.items():
                    for f in items['files']:
                        r += [f"{p.replace(f'{wd()}/fm', '')}/{f}"]
                del p, items
        del t
        return r

    def fullpath(self, path, status=False, di=None) -> object:
        r = path
        s = Status(204, 'Nothing happened')

        _wd = di if di else self._basedir

        def upone(_p, _c=0) -> str:
            _r, _t, _n = '', _p.split('/'), []
            _idx = _t.index('..')
            if _idx:
                for _i in range(0, len(_t)):
                    if _i != _t.index('..')-1 and _i != _t.index('..'):
                        _n += [_t[_i]]
                _r = '/' if _n and '/'.join(_n) == '' else '/'.join(_n)
            if '..' in _r:
                _c += 1
                _r = upone(_r, _c)
            if _idx == 0 and _c > 0:
                _r = '/'
            return _r

        if isinstance(path, str):
            if path.startswith('..'):
                r = upone(f"{_wd}/{path}")
            elif '..'  in path:
                r = upone(path)
            elif path.startswith('.'):
                if len(path) == 1 or (len(path) > 1 and path[1] == '/'):
                    r = path.replace('.', f"{_wd}")
                else:
                    r = f"{_wd}/{path}"
            elif path.endswith('/.'):
                r = path[:-2]
            elif path and not path.startswith('/'):
                r = f"{_wd}/{path}"
        if self.exists(r):
            s.code = 200
            s.message = 'Parsing attempted (successfully).'

        if status:
            return r, s
        else:
            return r

    def is_dir(self, path) -> tuple[bool, Status]:
        ...

    def latest(self, directory=None, fn_pattern=None, fn_only=False, path=None,
               ret=None):
        """
        See ts_based_file().
        :param directory: provide path
        :param fn_pattern: filter based on filename pattern
        :param fn_only: returns list [] of filenames only
        :return: directory, filename, timestamp
        """
        if not ret:
            ret = self._output_fmt
        if path and not directory:
            directory = path
        r = self._ts_sorted_file(
            'latest', directory=directory, fn_pattern=fn_pattern,
            fn_only=fn_only, ret=ret)
        if fn_only and ret == 'list' and len(r) > 0:
            return r[0]
        return r

    def ls(self, directory=None, fn_pattern=None, fn_only=False, path=None,
           ret=None):
        """
        See ts_based_file().
        :param directory: provide path
        :param fn_pattern: filter based on filename pattern
        :param fn_only: returns list [] of filenames only
        :return: directory, filename, timestamp
        """
        if not ret:
            ret = self._output_fmt
        if path and not directory:
            directory = path
        if not path and not directory:
            directory = self._basedir
        return self._ts_sorted_file(
            'list', directory=directory, fn_pattern=fn_pattern, fn_only=fn_only,
            ret=ret)

    def mkdirs(self, path) -> Status:
        s = Status(204, 'Nothing happened.')
        path = self.fullpath(path)
        if path:
            try:
                os.makedirs(path, exist_ok=True)
                s.code = 200
                s.message = 'OK'
            except Exception as e:
                s.code = 500
                s.message = f"fm.mkdirs() : Error ocurred. : {e}"
                log.error(s.message)
        return s

    def move(self, fn, src, dst):
        """
        Move file.
        :param fn: filename
        :param src: source path (only)
        :param dst: destination path (only)
        :return: True or False
        """
        r = False

        def newfilename(fnum):  # -- add <filename>_1[+n]
            if fnum == 0:
                _r = fn
            else:
                try:
                    nfn, ext = fn.split('.')
                    _r = f"{nfn}_{fnum}.{ext}"
                except Exception as e:
                    _r = f"{fn}_{fnum}"
                    log.error(f"Error: {e}")
            return _r

        def do_move(fnum=0):
            _r = False
            new_fn = newfilename(fnum)
            if not self.exists(f"{dst}/{new_fn}"):
                if self.exists(f"{src}/{fn}"):
                    os.rename(f"{src}/{fn}", f"{dst}/{new_fn}")
                    log.info(f"moved: [{src}/{fn}] to [{dst}/{new_fn}]")
                    _r = True
            else:
                fnum += 1
                _r = do_move(fnum)
            return _r

        # -- move files (recursively avoid name conflict)
        if src and dst:
            r = do_move()

        return r

    def oldest(self, directory=None, fn_pattern=None, fn_only=False, path=None,
               ret=None):
        """
        See ts_based_file().
        :param directory: provide path
        :param fn_pattern: filter based on filename pattern
        :param fn_only: returns list [] of filenames only
        :return: directory, filename, timestamp
        """
        if not ret:
            ret = self._output_fmt
        if path and not directory:
            directory = path
        r = self._ts_sorted_file(
            'oldest', directory=directory, fn_pattern=fn_pattern, fn_only=fn_only,
            ret=ret)
        if fn_only and ret == 'list' and len(r) > 0:
            return r[0]
        return r

    def pwd(self) -> str:
        """
        Returns current working directory
        """
        return self._basedir

    def reset(self, indir=None, outdir=None, arcdir=None, errdir=None, \
        known_dir=None, bucket=None) -> None:
        """
        Reset all state.
        """
        self._bucket = bucket if bucket else ''
        self._basedir = f"{envar('PWD')}"
        self.known_dir = known_dir
        self._output_fmt = 'list'
        self.ARCHIVE = arcdir
        self.ERRORED = errdir
        self.INPUT = indir
        self.OUTPUT = outdir
        return

    def retainer(self, directory, fn, retain) -> None:
        """
        Function to apply retention policy.
        :param directory: base path
        :param fn: file names containing substring
        :param ret_d: number of files to retain
        :return None: no return values
        """
        if retain > 0:
            del_list = self._ts_sorted_file('list', directory, \
                fn_pattern=f".*{fn}.*")
            if len(del_list) > retain:

                # -- unpack filename
                t = []
                for f in del_list:
                    t += [f[1]]
                del_list = t[:len(t)-retain]
                log.debug(f"list of file to delete: {del_list}")

                self.del_files(directory, del_list)
                del del_list, t

            log.info(f"applied retention policy: {directory}")
        return

    @deprecated
    def setbucket(self, dirname) -> None:
        """
        Deprecated to follow functions naming convention.
        Use set_bucket() instead.
        """
        self.set_bucket(dirname)
        return

    def set_bucket(self, dirname, auto_create=True) -> None:
        """
        Add a "bucket" to directory structure.
        :param dirname: name to set the subdirectory
        :return None: no return values
        """
        if not self._bucket:
            self._bucket = str(dirname)
            self.dir_struct(auto_create=auto_create)
            log.info(f"Bucket is now set to: {self._bucket}.")
        else:
            log.info(f"Buckets cannot be reset to a different name ({dirname}). "
                     f'Currently set to "{self._bucket}"')
        return

    def set_returns(self, ret='dict') -> None:
        """
        Set data output format to 'list', 'dict' or 'json' (default value: list).
        """
        if ret:
            self._output_fmt = ret
        return

    def touch(self, fn, time=None) -> None:
        func = "[common.fm][touch]"
        path = self.fullpath(fn)
        try:
            with open(path, 'a') as f:
                os.utime(f.name, time)
        except:
            log.error(f"{func} : Couldn't touch file: {fn}")
        return

    @deprecated
    def ts_sorted_file(self, req='latest', directory=None, fn_pattern=None, fn_only=False):
        return self._ts_sorted_file(req, directory, fn_pattern, fn_only)

    def _ts_sorted_file(self, req='latest', directory=None, fn_pattern=None,
                        fn_only=False, ret=None):
        """
        Look for the latest or oldest modified date from files in directory.
        :param action: 'latest' or 'oldest'
        :param directory: provide path
        :param fn_pattern: filter based on filename pattern
        :param fn_only: returns list [] of filenames only
        :param ret: change type of return values to "list of objects[dict, json]"
                    or "list of list"
        :return: list of [filename, timestamp], list of [<dict>] or list of [<json>]
        """
        r = []

        if not ret:
            ret = self._output_fmt
        if not directory:
            directory = self.INPUT if self.INPUT else self.pwd()
        directory = self.fullpath(directory)

        # -- build file list
        log.debug(f"directory: {directory}")
        log.debug(f"path-exists: {'yes' if self.exists(directory) else 'no'}")
        if directory and self.exists(directory):
            t = []

            # f_list = sorted([[int(os.stat(os.path.join(directory, f)).st_ctime), f] \
            #     for f in os.listdir(directory)])

            f_list = []
            for f in os.scandir(directory):
                ctime = int(os.stat(os.path.join(directory, f.name)).st_ctime)
                if ret == 'list':
                    f_list += [[ctime, f.name]]
                else:
                    f_list += [{
                        'filename': f.name,
                        'is_dir': True if f.is_dir(follow_symlinks=True) else False,
                        'is_symlink': True if f.is_symlink() else False,
                        'size': f.stat().st_size,
                        'stats': {
                            'atime': int(f.stat().st_atime),
                            'ctime': int(f.stat().st_ctime),
                            'mtime': int(f.stat().st_mtime)}
                    }]

            if not ret == 'list':
                if f_list:
                    f_list.sort(key=lambda x: x['filename'])
                if ret == 'json':
                    r = json.dumps(f_list, indent=4)
                else:
                    r = f_list
            else:
                f_list = sorted(f_list)

                if fn_pattern:
                    for n in sorted(f_list):
                        if re.search(fn_pattern, n[1]):
                            t += [[n[0], n[1]]]
                elif f_list:
                    t = f_list
                del f_list

                # -- apply filter
                if req == 'list':
                    r = t
                elif req == 'latest' and t:
                    r = [t[len(t)-1][0], t[len(t)-1][1]]
                elif req == 'oldest' and t:
                    r = [t[0][0], t[0][1]]
                del t

                # -- return simplified list
                if fn_only and ret == 'list' and r:
                    if req in ['latest', 'oldest']:
                        r = [r]
                    r = [x[1] for x in r]
        return r

    def walk(self, path=None, ret=None):
        res, _ = self.crawl_dir(path, ret)
        return res


fm = FileManager()
