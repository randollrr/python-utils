"""
Library to quickly/easily connect to MongoDB and using CRUD functionalities
in a frictionless way.
"""
__authors__ = ['randollrr']
__version__ = '1.2.4'

import json
import os

from pymongo import MongoClient
from pymongo.cursor import Cursor
from pymongo.database import Collection, Database
from bson import ObjectId, SON

from auto_utils import config, log


class MongoDB:
    def __init__(self, db_config=None, collection=None, db=None, collection_obj=None, db_obj=None):
        """
        Create database connection.

        :param db_config: configuration object map
        :param collection: existing pymongo collection object
        :param db: existing pymongo db object
        """
        self.collection = collection_obj
        self.db = db_obj
        collection_name = collection
        db_name = db
        self.client = None
        self.connected = False

        # -- validate passing objects
        if db_obj and isinstance(db_obj, Database):
            self.client = db_obj.client
        if db_obj and not isinstance(db_obj, Database):
            log.error('db_obj: {} is not a Database object'.format(type(db_obj)))
            return
        if collection_obj and not isinstance(collection_obj, Collection):
            log.error('collection_obj: {} is not a Collection object'.format(type(collection_obj)))
            return

        # -- database basic config
        if db_config is None and not self.db and not self.collection:
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
        if not db_name and not self.db:
            if db_config.get('database'):
                self.db = self.client[db_config['database']]
            else:
                self.db = self.client['test_db']
        elif db_name and not self.db:
            self.db = self.client[db_name]

        # -- setup collection
        if not collection_name and self.db:
            if db_config and db_config.get('collection'):
                self.collection = self.db[db_config['collection']]
            elif not self.collection:
                self.collection = self.db['test']
        elif collection_name and self.db:
            self.collection = self.db[collection_name]
        
        self.status()
        if self.connected:
            if collection_obj and db_obj:
                log.info('Using existing connection: {}@{}'.format(self.db.name, self.client.HOST))
            else:
                log.info('CONNECTED to {}@{}'.format(self.db.name, self.client.HOST))
        else:
            log.info('NOT CONNECTED.')

    def close(self):
        if self.status():
            self.client.close()
            self.connected = False
            log.info('DISCONNECTED.')

    def status(self):
        r = False
        if self.client and self.client.server_info():
            if isinstance(self.db.name, str):
                r = self.connected = True
        return r


class MongoCRUD:
    """
    Provide basic CRUD functionalities.
    """

    def __init__(self, collection=None, db=None, collection_obj=None, db_obj=None):
        self.connector = MongoDB(collection=collection, db=db, collection_obj=collection_obj, db_obj=db_obj)
        self.collection = self.connector.collection

    def cd(self, collection=None, db=None):
        """
        Change collection and/or database.
        :param collection: collection name to change
        :param db: database name to change (collecion is required)
        """
        if collection and self.connector.connected:
            if db:
                self.collection = self.connector.db.client[db][collection]
                log.info('Using database: {}'.format(self.connector.db.name))
            else:
                self.collection = self.connector.db[collection]    
                log.info('Using collection: {}.{}'.format(self.connector.db.name, self.collection.name))

    
    def create(self, doc=None, collection=None, db=None):
        """
        Insert object(s).
        :param doc: data to be inserted.
        :param collection: to change collection/table
        :param db: to change database
        """
        self.cd(collection, db)
        count = 0
        r = None
        c = 204
        m = 'Nothing happened.'
        
        try:
            ins = None
            if isinstance(doc, dict):
                ins = self.collection.insert_one(doc)
                r = self._decode_objectid(ins.inserted_id)
                count = 1 if r else 0
            elif isinstance(doc, list):
                ins = self.collection.insert_many(doc)
                r = ins.inserted_ids
                count = len(r)
            if r and ins:
                c = 201
                m = 'Data inserted.'
                log.info('create_count: {}, create_ack: {}'.format(count, ins.acknowledged))
        except Exception as e:
            c = 500
            m = 'Server Error: {}'.format(e)
        return self._response(r, c, m)

    def read(self, where=None, collection=None, db=None, projection=None, sort=None, aggr_cols=None, aggr_type=None, like=None):
        """
        Read <database>.<collection>.
        :param where: filter object to look for
        :param collection: to change collection/table
        :param db: to change database
        :param projection: fields to return in response i.e. {'name': true, 'department': true}
        :param aggr_cols: fields to group by ['name', 'department', 'salary']
        :param aggr_type: 'count', 'sum' i.e. aggr_type={'count': 'salary'} or aggr_type={'sum': 'salary'}
        :param like: use find() with $regex i.e. like={'employe_name': '^Ran'}
        """
        self.cd(collection, db)
        r = None
        c = 404
        m = 'No data returned.'
        doc_count = 0
        statement = []
        
        try:
            # -- build statement            
            if where:
                self._encode_objectid(where)
                for k in where:
                    if where[k] is None:
                        statement += [(k, {'$exist': False})]
                    else:
                        statement += [(k, where[k])]
            else:
                statement += [('_id', {'$exists': True})]
    
            # if isinstance(aggr_cols, list):
            #     if isinstance(aggr_type, dict):
            #         pass  # sum
            #     else:
            #         pass  # count
            
            log.info('retrieving doc(s) like: {}{}'.format(dict(statement), \
                ', {}'.format(projection) if projection else ''))

            # -- execute statement
            if isinstance(sort, dict):
                s_list = []
                for k in sort:
                    s_list += [(k, sort[k])]
                data = self.collection.find(SON(statement), projection).sort(s_list)
                del s_list
            else:
                data = self.collection.find(SON(statement), projection)

            # -- collect result
            for _ in data:
                doc_count += 1
            if doc_count > 0:
                data.rewind()
                r = data
                c = 200
                m = 'OK'
            log.info('read_count: {}'.format(doc_count))
        
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
        log.debug('update: {}'.format(doc))
        self.cd(collection, db)
        r = []
        c = 204
        m = 'Nothing happened.'
        
        try:
            if isinstance(doc, dict):
                self._encode_objectid(doc)
                obj = self.collection.replace_one({'_id': doc['_id']}, doc)
                log.info('update_match_count: {}, update_mod: {}, update_ack: {}'.format(
                    obj.matched_count, obj.modified_count, obj.acknowledged))
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
        self.cd(collection, db)
        r = []
        c = 204
        m = 'Nothing happened.'
        
        log.debug('delete doc(s) like: {}'.format(where))
        try:
            if where:
                if isinstance(where, dict):
                    where = [where]
                
                statement = []
                if isinstance(where, list):
                    for f in where:
                        if not isinstance(f, dict):
                            statement += [self._encode_objectid({'_id': f})]
                            r += [str(f)]
                        else:
                            statement += [self._encode_objectid(f)]
                    
                    for s in statement:
                        obj = self.collection.delete_one(s)
                        log.info('delete_count: {}, delete_ack: {}'.format(obj.deleted_count, obj.acknowledged))
                        r += [{'statement': s, 'delete_count': obj.deleted_count, 'delete_ack':obj.acknowledged}]
                c = 410
                m = 'Item(s) deletion have been executed.'
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
            if type(data) in [int, str, dict]:
                r['data'] += [self._decode_objectid(data)]
            elif type(data) in [Cursor, list]:
                for d in data:
                    r['data'] += [self._decode_objectid(d)]
            else:
                r['data'] = []
                rcode = 500
                message = 'Could not format data for response object ({}).'.format(type(data))
        
        r['status'] = {'code': rcode, 'message': message, 'records': len(r['data'])}
        log.debug('response: {}'.format(r))
        return r


db = MongoDB()
dao = MongoCRUD(collection_obj=db.collection, db_obj=db.db)
