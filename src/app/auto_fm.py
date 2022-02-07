import os
import re

from auto_utils import deprecated, log, wd

__authors__ = ['randollrr']
__version__ = '2.4.1'


class FileManager:
    """
    Implement methods to manipulate file(s) with common automation operations.
    """

    def __init__(self, indir=None, outdir=None, arcdir=None, errdir=None, \
        known_dir=None, bucket=None):
        self.bucket = bucket if bucket else ''
        self.basedir = './fm'
        self.filename = None
        self.known_dir = known_dir

        self.ARCHIVE = arcdir
        self.ERRORED = errdir
        self.INPUT = indir
        self.OUTPUT = outdir

    def del_dir(self, path):
        """
        Delete directory provided.
        :param path: directory (only)
        :return: True or False
        """
        r = False
        if self.exists(path):
            try:
                if self.basedir == '{}/fm'.format(path):
                    os.rmdir(self.basedir)
                if self.bucket and self.bucket in path:
                    os.rmdir(path)
                    path = path.replace(self.bucket, '')
                os.rmdir(path)
                r = True
                log.info('remove dir: {}'.format(path))
            except Exception as e:
                    log.error("Couldn't remove directory: {}".format(e))
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
                        log.info('deleted: {}/{}'.format(path, fn))
                        r = True
                    except Exception as e:
                        log.error("Couldn't remove file: {}".format(e))
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
            self.basedir = '{}/fm'.format(path)
        u_path = False
        if not self.known_dir:
            self.known_dir = ['archive', 'errored', 'input', 'output']
            u_path = True
        if known_dir:
            self.known_dir = known_dir

        log.info('validate directory structure for: {}'.format(self.basedir))
        try:
            i = 0
            for d in self.known_dir:
                n_path = os.path.join(self.basedir, d, self.bucket)
                if u_path:
                    update_path(d, n_path)
                if not os.path.exists(n_path):
                    log.info('creating: {}'.format(n_path))
                    os.makedirs(n_path, exist_ok=True)
            r = True
        except Exception as e:
            log.info("Couldn't setup directory structure.\n{}".format(e))
        return r

    def exists(self, path=None):
        r = False
        if isinstance(path, str) and os.path.exists(path):
            r = True
        return r

    def latest(self, directory=None, fn_pattern=None, fn_only=False):
        """
        See ts_based_file().
        :param directory: provide path
        :param fn_pattern: filter based on filename pattern
        :param fn_only: returns list [] of filenames only
        :return: directory, filename, timestamp
        """
        r = self._ts_sorted_file(
            'latest', directory=directory, fn_pattern=fn_pattern, fn_only=fn_only)
        if fn_only and len(r) > 0:
            return r[0]
        return r

    def ls(self, directory=None, fn_pattern=None, fn_only=False):
        """
        See ts_based_file().
        :param directory: provide path
        :param fn_pattern: filter based on filename pattern
        :param fn_only: returns list [] of filenames only
        :return: directory, filename, timestamp
        """
        return self._ts_sorted_file(
            'list', directory=directory, fn_pattern=fn_pattern, fn_only=fn_only)

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
                    ret = '{}_{}.{}'.format(nfn, fnum, ext)
                except Exception as e:
                    ret = '{}_{}'.format(fn, fnum)
                    log.debug('Error: {}'.format(e))
            return ret

        def do_move(fnum=0):
            ret = False
            new_fn = newfilename(fnum)
            if not self.exists('{}/{}'.format(dst, new_fn)):
                if self.exists('{}/{}'.format(src, fn)):
                    os.rename('{}/{}'.format(src, fn), '{}/{}'.format(dst, new_fn))
                    log.info('moved: [{}/{}] to [{}/{}]'.format(src, fn, dst, new_fn))
                    ret = True
            else:
                fnum += 1
                ret = do_move(fnum)
            return ret

        # -- move files (recursively avoid name conflict)
        if src and dst:
            r = do_move()

        return r

    def oldest(self, directory=None, fn_pattern=None, fn_only=False):
        """
        See ts_based_file().
        :param directory: provide path
        :param fn_pattern: filter based on filename pattern
        :param fn_only: returns list [] of filenames only
        :return: directory, filename, timestamp
        """
        r = self._ts_sorted_file(
            'oldest', directory=directory, fn_pattern=fn_pattern, fn_only=fn_only)
        if fn_only and len(r) > 0:
            return r[0]
        return r

    def retainer(self, directory, fn, retain):
        """
        Function to apply retention policy.
        :param directory: base path
        :param fn: file names containing substring
        :param ret_d: number of files to retain
        """
        if retain > 0:
            del_list = self._ts_sorted_file('list', directory, \
                fn_pattern='.*{}.*'.format(fn))
            if len(del_list) > retain:

                # -- unpack filename
                t = []
                for f in del_list:
                    t += [f[1]]
                del_list = t[:len(t)-retain]
                log.debug('list of file to delete: {}'.format(del_list))

                self.del_files(directory, del_list)
                del del_list, t

            log.info('applied retention policy: {}'.format(directory))

    def setbucket(self, dirname):
        """
        Add a "bucket" to directory structure.
        :param dirname: name to set the subdirectory
        """
        if not self.bucket:
            self.bucket = str(dirname)
            self.dir_struct()
            log.info('Bucket is now set to: {}.'.format(self.bucket))
        else:
            log.info('Buckets cannot be reset to a different name ({}). '
                     'Currently set to "{}"'.format(dirname, self.bucket))

    def touch(self, fn, time=None):
        with open(fn, 'a') as f:
            os.utime(f.name, time)

    @deprecated
    def ts_sorted_file(self, req='latest', directory=None, fn_pattern=None, fn_only=False):
        return self._ts_sorted_file(req, directory, fn_pattern, fn_only)

    def _ts_sorted_file(self, req='latest', directory=None, fn_pattern=None, fn_only=False):
        """
        Look for the latest or oldest modified date from files in directory.
        :param action: 'latest' or 'oldest'
        :param directory: provide path
        :param fn_pattern: filter based on filename pattern
        :param fn_only: returns list [] of filenames only
        :return: filename, timestamp
        """
        r = []

        if not directory and self.INPUT:
            directory = self.INPUT

        # -- build file list
        log.debug('directory: {}'.format(directory))
        log.debug('directory exists: {}'.format(self.exists(directory)))
        if directory and self.exists(directory):
            t = []
            l = sorted([[int(os.stat(os.path.join(directory, f)).st_ctime*1000), f] \
                for f in os.listdir(directory)])
            if fn_pattern:
                for n in sorted(l):
                    if re.search(fn_pattern, n[1]):
                        t += [[n[0], n[1]]]
            elif l:
                t = l
            del l

            # -- apply filter
            if req == 'list':
                r = t
            elif req == 'latest' and t:
                r = [t[len(t)-1][0], t[len(t)-1][1]]
            elif req == 'oldest' and t:
                r = [t[0][0], t[0][1]]
            del t

            # -- return simplified list
            if fn_only:
                if req in ['latest', 'oldest']:
                    r = [r]
                r = [x[1] for x in r]
        return r

fm = FileManager()
