import os
import re

from auto_utils import log

__authors__ = ['randollrr']
__version__ = '2.1'


class FileManager:
    """
    Implement methods to manipulate file(s) with common automation operations.
    """

    def __init__(self, indir=None, outdir=None, archive=None):
        self.filename = None
        self.src = indir
        self.dst = outdir
        self.arc = archive

    @staticmethod
    def delete_files(path, files):
        """
        Delete list of files provided.
        :param path: directory (only)
        :param files: [list of files]
        :return: True or False
        """
        if FileManager.exists(path):
            if type(files) is list:
                for fn in files:
                    try:
                        os.remove(os.path.join(path, fn))
                        r = True
                    except Exception as e:
                        r = False
                        log.error(f"Couldn't remove file: {fn}")
                        log.debug(e)

    @staticmethod
    def dir_struct(path, known_dir=None):
        """
        Check directory structure. If not valid, create structure.
        :param path: filesystem full path
        :param known_dir: list of dir paths
        :return: True or False
        """
        r = False
        if not known_dir:
            known_dir = ['daily', 'weekly', 'monthly']

        log.info(f'check directory structure for: {path}')
        try:
            for d in known_dir:
                if not os.path.exists(os.path.join(path, d)):
                    log.info(f'Creating: {path}/{d}')
                    os.makedirs(os.path.join(path, d), exist_ok=True)
            r = True
        except Exception as e:
            log.info(f"Couldn't setup directory structure.\n{e}")
        return r

    @staticmethod
    def exists(fn=None):
        r = False
        if os.path.exists(fn):
            r = True
        return r

    def latest(self, directory=None, fn_pattern=None):
        """
        See ts_based_file().
        :param directory: provide path
        :param fn_pattern: filter based on filename pattern
        :return: directory, filename, timestamp
        """
        return self.ts_sorted_file('latest', directory=directory, fn_pattern=fn_pattern)

    @staticmethod
    def move(fn, src, dst):
        """
        Move file.
        :param fn: filename
        :param src: source path (only)
        :param dst: destination path (only)
        :return: True or False
        """
        r = None

        def newfilename(fnum):  # -- add <filename>_1[+n]
            if fnum == 0:
                ret = fn
            else:
                try:
                    nfn, ext = fn.split('.')
                    ret = '{}_{}.{}'.format(nfn, fnum, ext)
                except Exception as e:
                    ret = '{}_{}'.format(fn, fnum)
                    log.debug(f'Error: {e}')
            return ret

        def do_move(fnum=0):
            ret = False
            new_fn = newfilename(fnum)
            if not FileManager.exists('{}/{}'.format(dst, new_fn)):
                if FileManager.exists('{}/{}'.format(src, fn)):
                    os.rename('{}/{}'.format(src, fn), '{}/{}'.format(dst, new_fn))
                    ret = True
            else:
                fnum += 1
                do_move(fnum)
            return ret

        if src and dst:
            r = do_move()
        return r

    def oldest(self, directory=None, fn_pattern=None):
        """
        See ts_based_file().
        :param directory: provide path
        :param fn_pattern: filter based on filename pattern
        :return: directory, filename, timestamp
        """
        return self.ts_sorted_file('oldest', directory=directory, fn_pattern=fn_pattern)

    def ts_sorted_file(self, action='latest', directory=None, fn_pattern=None):
        """
        Look for the latest or oldest modified date from files in directory.
        :param action: 'latest' or 'oldest'
        :param directory: provide path
        :param fn_pattern: filter based on filename pattern
        :return: filename, timestamp
        """
        r = (None, None)
        final = None
        if not directory:
            if self.src:
                directory = self.src

        # -- build file list
        log.debug(f'directory: {directory}')
        log.debug(f'directory exists: {self.exists(directory)}')
        if directory and self.exists(directory):
            t = []
            l = [[int(os.stat(os.path.join(directory, f)).st_ctime*1000), f] for f in os.listdir(directory)]
            if fn_pattern:
                for n in sorted(l):
                    if re.search(fn_pattern, n[1]):
                        t += [[n[1], n[0]]]
            elif l:
                t = sorted(l)

            # -- apply filter
            if action == 'list':
                return t
            if action == 'latest':
                final = t[len(t) - 1][0], int(t[len(t) - 1][1])
            elif action == 'oldest':
                final = t[0][0], int(t[0][1])
            if final:
                r = final[0], final[1]
            del l, t, action, final
        return r


# changelog
# 1.0 initial release with ept file parser
# 2.0 optimized move.do_move()
#     added now return file ts in latest()
#     ported dir_struct() from mongobak.py
#     optimized latest() --> ts_sorted_file()
#     added oldest()
#     added delete()
