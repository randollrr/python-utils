"""
Extracted from Utils (which is intended to be a swiss-army-knife toolbox that houses boilerplate codes)
for many apps or scripts. A generic API to access:
    * databases:
      - oracle
      - mysql
      - and mongodb
"""
__authors__ = ['randollrr']
__version__ = '1.6.0'

import json

try:
    import MySQLdb as mysql  # TODO: only import if necessary or in config file
    import cx_Oracle as oracle  # TODO: only import if necessary or in config file
    import yaml
except ImportError:
    pass

from utils import Config
from utils import log


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
                host=config['database']['host'],
                user=config['database']['user'],
                passwd=config['database']['password'],
                db=config['database']['schema'])
            log.info('Database.connect(): Connected to database via %s@%s '
                     'on %s.' % (
                        config['database']['user'],
                        config['database']['schema'],
                        config['database']['host']))
            self._state = True
        except Exception as e:
            log.error('Database.connect(): Unable to connect to the '
                      'database. [%s]' % e)

        # TODO: Add support to "Database" to manage connection pool with multiple databases connections.
        """
        db_tns = cx_Oracle.makedsn('<host>', 1521, '<schema>')
        db_cx  = cx_Oracle.connect('<user>','<password>',db_tns)
        db_cur = db_cx.cursor()
        """

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
        def decimal(num):
            ret = str(num)
            if num is not None:
                n = len(str(num).split('.'))
                if 1 < n < 3:
                    ret = float(num)
            return ret

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
        r = json.dumps(model, indent=4, sort_keys=True, default=decimal)
        return r
