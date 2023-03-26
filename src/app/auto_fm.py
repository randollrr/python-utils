import json
import os
import re

from auto_utils import deprecated, log, envar_in, Status

__authors__ = ['randollrr']
__version__ = '2.5.0'


class FileManager:
    """
    Utility (interface) to facilitate REST-based file-system management. Implements
    methods to manipulate file(s) with common automation operations.
    """

    def __init__(self, indir=None, outdir=None, arcdir=None, errdir=None, \
        known_dir=None, bucket=None):
        self._bucket = bucket if bucket else ''
        self._basedir = f"{envar_in('((env:PWD))')}"
        # self.filename = None
        self.known_dir = known_dir

        self.ARCHIVE = arcdir
        self.ERRORED = errdir
        self.INPUT = indir
        self.OUTPUT = outdir

    def cd(self, newpath) -> Status:
        s = Status(204, 'Nothing happened')
        n, s_fp = self.fullpath(newpath)
        if s_fp == 200:
            self._basedir = n
            s.code = 200
            s.message = f"new directory: {n}"
        else:
            s.code = s_fp.code
            s.message = s_fp.message
        return s

    def del_dir(self, path):
        """
        Delete directory provided (as long as it's not a set bucket).
        :param path: directory (only)
        :return: True or False
        """
        r = False
        if self.exists(path):
            try:
                if self._basedir == f"{path}/fm":
                    os.rmdir(self._basedir)  # remove "/fm/" 1st before "dirstruct"
                if self._bucket and self._bucket in path:
                    # os.rmdir(path)
                    # path = path.replace(self._bucket, '')
                    log.warn(f"fm.del_dir(): Cannot delete {self._bucket} in path provided. "
                             f"Use fm.del_bucket() instead.")
                os.rmdir(path)
                r = True
                log.info(f"remove dir: {path}")
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

            if isinstance(files, list):
                for fn in files:
                    try:
                        os.remove(os.path.join(path, fn))
                        log.info(f"deleted: {path}/{fn}")
                        r = True
                    except Exception as e:
                        log.error(f"Couldn't remove file: {e}")
            else:
                log.debug('Expected a list of files or a path with flag "dir=True"')
        return r

    def dir_struct(self, path=None, known_dir=None):
        """
        Check directory structure. If not valid, create structure.
        :param path: filesystem full path
        :param known_dir: list of dir paths
        :return: True or False
        """
        r = False

        def update_path(_p, _np):
            if _p == 'archive':
                self.ARCHIVE = _np
            elif _p == 'errored':
                self.ERRORED = _np
            elif _p == 'input':
                self.INPUT = _np
            elif _p == 'output':
                self.OUTPUT = _np

        if path:
            self._basedir = f"{path}/fm"
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
                    os.makedirs(n_path)
                else:
                    log.info(f"already exists: {n_path}")
            r = True
        except Exception as e:
            log.error(f"Couldn't setup directory structure.\n{e}")
        return r

    def exists(self, path=None):
        r = False
        if isinstance(path, str) and os.path.exists(path):
            r = True
        return r

    def latest(self, directory=None, fn_pattern=None, fn_only=False, ret='list'):
        """
        See ts_based_file().
        :param directory: provide path
        :param fn_pattern: filter based on filename pattern
        :param fn_only: returns list [] of filenames only
        :return: directory, filename, timestamp
        """
        r = self._ts_sorted_file(
            'latest', directory=directory, fn_pattern=fn_pattern, fn_only=fn_only,
            ret='list')
        if fn_only and ret == 'list' and len(r) > 0:
            return r[0]
        return r

    def ls(self, directory=None, fn_pattern=None, fn_only=False, ret='list'):
        """
        See ts_based_file().
        :param directory: provide path
        :param fn_pattern: filter based on filename pattern
        :param fn_only: returns list [] of filenames only
        :return: directory, filename, timestamp
        """
        return self._ts_sorted_file(
            'list', directory=directory, fn_pattern=fn_pattern, fn_only=fn_only,
            ret='list')

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
                ret = fn
            else:
                try:
                    nfn, ext = fn.split('.')
                    ret = f"{nfn}_{fnum}.{ext}"
                except Exception as e:
                    ret = f"{fn}_{fnum}"
                    log.error(f"Error: {e}")
            return ret

        def do_move(fnum=0):
            ret = False
            new_fn = newfilename(fnum)
            if not self.exists(f"{dst}/{new_fn}"):
                if self.exists(f"{src}/{fn}"):
                    os.rename(f"{src}/{fn}", f"{dst}/{new_fn}")
                    log.info(f"moved: [{src}/{fn}] to [{dst}/{new_fn}]")
                    ret = True
            else:
                fnum += 1
                ret = do_move(fnum)
            return ret

        # -- move files (recursively avoid name conflict)
        if src and dst:
            r = do_move()

        return r

    def oldest(self, directory=None, fn_pattern=None, fn_only=False, ret='list'):
        """
        See ts_based_file().
        :param directory: provide path
        :param fn_pattern: filter based on filename pattern
        :param fn_only: returns list [] of filenames only
        :return: directory, filename, timestamp
        """
        r = self._ts_sorted_file(
            'oldest', directory=directory, fn_pattern=fn_pattern, fn_only=fn_only,
            ret='list')
        if fn_only and ret == 'list' and len(r) > 0:
            return r[0]
        return r

    def fullpath(self, path, di=None) -> tuple[str, Status]:
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
                r = path.replace('.', f"{_wd}")
            elif path.endswith('/.'):
                r = path[:-2]
        if r != path:
            s.code = 200
            s.message = 'Parsing attempted (successfully).'
        return r, s

    def pwd(self) -> str:
        """
        Returns current working directory
        """
        return self._basedir

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
        """Deprecated to follow snake case."""
        self.set_bucket(dirname)
        return

    def set_bucket(self, dirname) -> None:
        """
        Add a "bucket" to directory structure.
        :param dirname: name to set the subdirectory
        :return None: no return values
        """
        if not self._bucket:
            self._bucket = str(dirname)
            self.dir_struct()
            log.info(f"Bucket is now set to: {self._bucket}.")
        else:
            log.info(f"Buckets cannot be reset to a different name ({dirname}). "
                     f'Currently set to "{self._bucket}"')
        return

    def touch(self, fn, time=None) -> None:
        with open(fn, 'a') as f:
            os.utime(f.name, time)
        return

    @deprecated
    def ts_sorted_file(self, req='latest', directory=None, fn_pattern=None, fn_only=False):
        return self._ts_sorted_file(req, directory, fn_pattern, fn_only)

    def _ts_sorted_file(self, req='latest', directory=None, fn_pattern=None,
                        fn_only=False, ret='list'):
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

        if not directory:
            directory = self._basedir

        # -- build file list
        log.debug(f"directory: {directory}")
        log.debug(f"directory exists: {self.exists(directory)}")
        if directory and self.exists(directory):
            t = []
            f_list = sorted([[int(os.stat(os.path.join(directory, f)).st_ctime), f] \
                for f in os.listdir(directory)])
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

fm = FileManager()
