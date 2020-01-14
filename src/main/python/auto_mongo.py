"""
Library to quickly/easily connect to MongoDB and using CRUD functionalities
frictionlessly.
"""
__authors__ = ['randollrr']
__version__ = '1.0'

import json
import os

from pymongo import MongoClient
from bson import ObjectId, SON

from auto_utils import config
from auto_utils import log


class MongoDB:
    def __init__(self, db_config=None, collection=None, db=None):
        global config

        self.client = None
        self.db = None
        self.collection = None
        self.connected = False

        if db_config is None:
            if os.environ.get('APP_RUNTIME_CONTEXT') == 'dev':
                db_config = config['mongo.dev']
                self.environ = 'dev'
            elif os.environ.get('APP_RUNTIME_CONTEXT') == 'qa':
                db_config = config['mongo.qa']
                self.environ = 'qa'
            else:
                db_config = config['mongo.prod']
                self.environ = 'prod'
            log.info('Using mongo.{} configuration.'.format(self.environ))
        else:
            log.info('Using db_config provided: {}'.format(db_config))
        
        if db_config:
            self.client = MongoClient(
                'mongodb://{}:{}/'.format(db_config['host'], db_config['port']),
                username=db_config['username'],
                password=db_config['password'],
                authSource=db_config['authenticationDatabase'])
            # -- setup database
            if db:
                self.db = self.client[db]
            else:
                if db_config.get('database'):
                    self.db = self.client[db_config['database']]
                else:
                    self.db = self.client['admin']
            # -- setup collection
            if collection:
                self.collection = self.db[collection]
            else:
                if db_config.get('collection'):
                    self.collection = self.db[db_config['collection']]
                else:
                    self.collection = self.db['system.version']
            self.connected = True
        if self.connected:
            log.info('CONNECTED to {}@{}'.format(self.db.name, db_config['host']))
        else:
            log.info('NOT CONNECTED. (db={}, host={})'.format(self.db.name, db_config['host']))

    def close(self):
        if self.status():
            self.client.close()
            self.connected = False
            log.info('DISCONNECTED.')

    def status(self):
        r = False
        if self.client.server_info():
            if isinstance(self.db.name, str):
                r = self.connected = True
        return r


class MongoCRUD:
    """
    Provide basic CRUD functionalities.
    """

    def __init__(self, collection=None, db=None):
        self.connector = MongoDB(collection=collection, db=db)
        self.collection = self.connector.collection

    def create(self, doc=None, collection=None, db=None):
        """
        Insert object(s).
        :param doc: data to be inserted.
        :param collection: to change collection/table
        :param db: to change database
        """
        log.info('inserting doc: {}'.format(doc))
        self._update_session(collection, db)
        r = None
        c = 204
        m = 'Nothing happened.'
        
        try:
            ins = None
            if isinstance(doc, dict):
                ins = self.collection.insert_one(doc)
                r = [str(ins.inserted_id)]
                log.info('inserted: {}, {}'.format(ins.acknowledged, ins.inserted_id))
            elif isinstance(doc, list):
                ins = self.collection.insert_many(doc)
                r = [str(i) for i in ins.inserted_ids]
                log.info('inserted: {}, {}'.format(ins.acknowledged, r))
            if r:
                c = 201
                m = 'Data inserted.'
        except Exception as e:
            r = doc
            c = 500
            m = 'Server Error: {}'.format(e)
        return self._response(r, c, m)

    def read(self, where=None, collection=None, db=None, projection=None, aggr_cols=None, aggr_type=None, like=None):
        """
        Read <database>.<collection>.
        :param where: filter object to look for
        :param collection: to change collection/table
        :param db: to change database
        :param projection: fields to return in response
        :param aggr_cols: fields to group by ['name', 'department', 'salary']
        :param aggr_type: 'count', 'sum' i.e. aggr_type='count' or aggr_type={'sum': 'salary'}
        :param like: use find() with $regex i.e. like={'employe_name': '^Ran'}
        """
        self._update_session(collection, db)
        r = statement = None
        c = 404
        m = 'No data returned.'
        doc_count = 0

        try:
            if where:
                statement = where
            else:
                statement = {}
            log.info('retrieving doc(s) like: {}'.format(statement))
            
            if isinstance(aggr_cols, list):
                if isinstance(aggr_type, dict):
                    pass  # sum
                else:
                    pass  # count
                data = None
            elif isinstance(statement, dict):
                data = self.collection.find(statement, projection=projection)
                
            for _ in data:
                doc_count += 1
            if doc_count > 0:
                data.rewind()
                r = data
                c = 200
                m = 'OK'
            log.info('data: {} doc(s).'.format(doc_count))
        except Exception as e:
            r = statement
            c = 500
            m = 'Server Error: {}'.format(e)
        return self._response(r, c, m)

    def update(self, doc=None, collection=None, db=None, where=None, like=None, set=None):
        """
        :param doc: new version of database object to update
        :param collection: to change collection/table
        :param db: to change database
        :param where: criteria to locate database object i.e {'city': 'Atlanta}
        :param like: use filter with $regex i.e. like={'employe_name': '^Ran'}
        :param set: use $set to update field i.e. where={'_id': '5e1ab71ed4a0e6a7bdd5233f'}, set={'employe_name': 'Randoll'}
        """
        log.info('updating: {}'.format(doc))
        self._update_session(collection, db)
        r = []
        c = 204
        m = 'Nothing happened.'
        
        try:
            if isinstance(doc, dict):
                obj = self.collection.replace_one({'_id': doc['_id']}, doc)
                log.info('update(): ack: {}, match_count: {}, modified_count: {}, doc: {}'.format(
                    obj.acknowledged, obj.matched_count, obj.modified_count, doc))
                c = 200
                m = 'Document(s) updated.'
        except Exception as e:
            r = doc
            c = 500
            m = 'Server Error: {}'.format(e)
        return self._response(r, c, m)

    def delete(self, where=None, collection=None, db=None):
        """
        Remove document or object in document.
        :param statement: document/object to query to remove 
        :param collection: to change collection/table
        :param db: to change database
        :example:

            delete({'_id': '5e114ad941734d371c5f84b9'})
            delete([{'_id': '5e114ad941734d371c5f84b9'}, {'age': 25}])
            delete({'person.fname': 'Randoll'}   # delete document where {'person': {'fname': 'Randoll'}}
            delete({})                           # delete all in collection, not allowed
        """
        log.info('deleting doc(s) like: {}'.format(where))
        self._update_session(collection, db)
        r = []
        c = 204
        m = 'Nothing happened.'
        
        try:
            if where:
                if isinstance(where, dict):
                    where = [where]
                
                if isinstance(where, list):
                    statement = []
                    for f in where:
                        if not isinstance(f, dict):
                            statement += [self._encode_objectid({'_id': f})]
                            r += [str(f)]
                        else:
                            statement += [self._encode_objectid(f)]
                    
                    for s in statement:
                        obj = self.collection.delete_one(s)
                        log.info('delete: ack: {}, delete_count: {}, doc: {}'.format(obj.acknowledged, obj.deleted_count, s))
                r = statement
                c = 410
                m = 'Item(s) delete.'
        except Exception as e:
            r = where
            c = 500
            m = 'Server Error: {}'.format(e)
        return self._response(r, c, m)

    
    def _decode_objectid(self, o):
        r = o
        if isinstance(o, dict):
            if o.get('_id'):
                try:
                    o['_id'] = int(o['_id'])
                except:
                    o['_id'] = str(o['_id'])
                r = o
        else:
            r = str(o)
        return r
    
    def _encode_objectid(self, o):
        if isinstance(o, dict):
            if o.get('_id'):
                try:
                    o['_id'] = ObjectId(o['_id'])
                except:
                    try:
                        o['_id'] = int(o['_id'])
                    except:
                        pass    
        return o
    
    def _response(self, data=None, rcode=None, message=None):
        r = {'data': []}

        if data:
            if isinstance(data, str):
                r['data'] = list(self._decode_objectid(data))
            else:
                for d in data:
                    r['data'] += [self._decode_objectid(d)]
        
        r['status'] = {'code': rcode, 'message': message, 'records': len(r['data'])}
        log.debug('response: {}'.format(r))
        return r
    
    def _update_session(self, collection=None, db=None):
        if collection:
            if db:
                self.collection = self.connector.db.client[db][collection]
            else:
                self.collection = self.connector.db[collection]    
        log.info('Using collection: {}.{}'.format(self.connector.db.name, self.collection.name))
