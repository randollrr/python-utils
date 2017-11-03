"""
Utils is intended to be a swiss-army-knife toolbox that houses boilerplate codes
for many apps or scripts. A generic API to access:
    * databases,
    * config files,
    * logs,
    * email servers for notifications,
    * simple encryption, etc...

"""
__authors__ = ['randollrr', 'msmith8']
__version__ = '1.4.0'

import json
import logging
import os
import warnings
import yaml
from logging.handlers import RotatingFileHandler

try:
    import MySQLdb as mysql  # TODO: only import if necessary or in config file
    import cx_Oracle as oracle  # TODO: only import if necessary or in config file
except ImportError:
    pass


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""
    def new_func(*args, **kwargs):
        warnings.warn("Call to deprecated function {0}.".format(func.__name__),
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func


class Config:
    """
    Read and write configuration file(s). 2015.06.19|randollrr

        * specify UTILS_CONFIG_FILE envar for "config.yaml"
    """
    def __init__(self):
        self._state = False
        try:
            self.file = str(os.environ['UTILS_CONFIG_FILE'])
        except KeyError:
            print('    UTILS_CONFIG_FILE envar is not set. Using default "./config.yaml".')
            self.file = 'config.yaml'
        with open(self.file, 'r') as f:
            self.params = yaml.load(f)  # ToDO: should be read in Config class
            self._state = True

    def status(self):
        return self._state


class Database:
    """
    Create database connections -- Assuming connection info is in config.json
    file. 2012.05.31|randollrr
    """
    def __init__(self, pconn=None):
        self._conn_ct = 0
        self._conn = None
        self._state = False
        self._pconn = pconn

    def commit(self):
        try:
            self._conn.commit()
        except Exception as e:
            log.error('%s' % e)

    def connect(self):
        config = Config()
        if not config.status():
            log.error('Database.connect(): Unable to read database parameters '
                      'from the config file.')
            return
        try:
            self._conn = mysql.connect(
                host=config.params['database']['host'],
                user=config.params['database']['user'],
                passwd=config.params['database']['password'],
                db=config.params['database']['schema'])
            log.info('Database.connect(): Connected to database via %s@%s '
                     'on %s.' % (
                        config.params['database']['user'],
                        config.params['database']['schema'],
                        config.params['database']['host']))
            self._state = True
        except Exception as e:
            log.error('Database.connect(): Unable to connect to the '
                      'database. [%s]' % e)

        """
        db_tns = cx_Oracle.makedsn('ATSVLDB04.gsi.local', 1521, 'DELTEKTE')
        db_cx  = cx_Oracle.connect('vtis','ornuapp',db_tns)
        db_cur = db_cx.cursor()
        """

    def _decimal(self, num):
        r = str(num)
        if num is not None:
            n = len(str(num).split('.'))
            if 1 < n < 3:
                r = float(num)
        return r

    def disconnect(self):
        try:
            if self.status():
                self._conn.close()
                log.debug('Database.disconnect(): Disconnected from database.')
        except Exception as e:
            log.error('Database.disconnect(): Unable to disconnect to the '
                      'database. [%s]' % e)
        self._state = False

    def execute(self, stmt):
        cur = None
        try:
            if self.status():
                cur = self._conn.cursor()
                cur.execute(stmt)
                log.info(stmt)
            else:
                log.error('Could not execute SQL statement.')
        except Exception as e:
            log.error('  %s' % e)
        finally:
            if cur is not None:
                cur.close()
            del cur

    def exec_proc(self, stmt, args):
        cur = None
        try:
            if self.status():
                cur = self._conn.cursor()
                cur.callproc(stmt, args)
                log.debug('%s, %s' % (stmt, args))
            else:
                log.error('Could not execute stored procedure.')
        except Exception as e:
            log.error('%s' % e)
        finally:
            if cur is not None:
                cur.close()
            del cur

    def status(self):
        return self._state

    def query(self, stmt):
        rows = None
        cur = None
        try:
            if self.status():
                cur = self._conn.cursor()
                cur.execute(stmt)
                log.debug('Database.query(): %s' % stmt)
                rows = cur.fetchall()
            else:
                log.error('Database.query(): Could not query database, '
                          'connection is not active.')
        except Exception as e:
            log.error('%s' % e)
        finally:
            if cur is not None:
                cur.close()
            del cur
        return rows

    def tojson(self, model, query):
        if model is None or query is None:
            log.error('Database.tojson(): Received an invalid Model/Query.')
            return

        columns = model['meta'].keys()
        model['data'] = []
        model['status'] = {'code': 200,
                           'message': 'OK'}

        # -- build SQL statement
        stmt = "select distinct `%s` " % columns[0]
        for c in columns[1:]:
            stmt += ',`%s` ' % c
        stmt += query

        # -- map RDBMS data to dict
        try:
            # log.debug('Database.tojson(): %s' % stmt)
            rows = self.query(stmt.strip())
            if rows is not None and len(rows) > 0:
                for row in rows:
                    data = dict()
                    i = 0
                    for col in row:
                        data[columns[i]] = col
                        i += 1
                    model['data'].append(data)
                    del data
            else:
                log.error('Database.tojson(): row is None.')
                model['status'] = {'code': 404,
                                   'message': 'No data retrieved.'}
        except Exception as e:
            model['status'] = {'code': 500,
                               'message': 'Error while retrieving data.'}
            log.error('Database.tojson(): Error occurred. \n{0}'.format(e))

        # -- convert dict to json
        r = json.dumps(model, indent=4, sort_keys=True, default=self._decimal)
        return r


class Log:
    """
    Logging wrapper class for apps and scripts. 2016.02.10|randollrr
    """
    def __init__(self):
        config = Config()
        self.DEBUG = logging.DEBUG
        self.INFO = logging.INFO
        self.ERROR = logging.ERROR
        self.WARN = logging.WARN
        log_level = config.params['logging']['log-level']
        self.log_filename = '%s/%s.log' % (config.params['directories']['app-log'],
                                           config.params['system']['app-name'])
        file_handler = RotatingFileHandler(self.log_filename, maxBytes=1024000, backupCount=1)
        stream_handler = logging.StreamHandler()
        if log_level == "DEBUG":
            level = self.DEBUG
        elif log_level == "INFO":
            level = self.INFO
        elif log_level == "ERROR":
            level = self.ERROR
        elif log_level == "WARN":
            level = self.WARN
        else:
            level = self.DEBUG
        self.logger = logging.getLogger(config.params['system']['app-name'])
        self.logger.setLevel(level)
        formatter = logging.Formatter(
            '[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S +0000')
        stream_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)
        self.logger.addHandler(file_handler)

    def addhandler(self, handler):
        self.logger.addHandler(handler)

    def debug(self, msg):
        self.logger.debug(msg)

    def error(self, msg):
        self.logger.error(msg)

    def filename(self):
        return self.log_filename

    def gethandler(self):
        return self.logger.handlers

    def info(self, msg):
        self.logger.info(msg)

    def warn(self, msg):
        self.logger.warn(msg)


log = Log()


class Email_Client:
    """A simple client to send email via a local sendmail instance
    """
    def __init__(self):
        config = Config()
        self.SENDMAIL = config.params['sendmail']
        self.from_addr = self.SENDMAIL['from']
        self.to_addresses = self.SENDMAIL['stake_holders']

    def send_email(self, subject, body):
        p = os.popen("%s -t" % self.SENDMAIL['path'], "w")
        p.write("To: {0}\n".format(self.to_addresses))
        p.write("Subject: {0}\n".format(subject))
        p.write("From: {0}\n".format(self.from_addr))
        p.write("\n")  # blank line separating headers from body
        p.write(body)
        sts = p.close()
        if sts != 0:
            log.info("Sendmail exit status: {0}".format(sts))


"""
# TODO: Add support to "Database" to manage connection pool with multiple databases connections.
"""
