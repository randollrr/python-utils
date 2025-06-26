"""
Library to quickly/easily connect to MongoDB and using CRUD functionalities
in a frictionless way.
"""
__version__ = '1.5.0'

from copy import deepcopy
import os
from uuid import uuid4

from pymongo import MongoClient
from pymongo.cursor import Cursor
from pymongo.database import Collection, Database
from pymongo.errors import ServerSelectionTimeoutError
from bson import ObjectId, SON

from common.utils import config, log, ts


class MongoDB:
    def __init__(self, db_config=None, collection=None, db=None, collection_obj=None, db_obj=None, db_client=None):
        """
        Create database connection.

        :param db_config: configuration object map
        :param collection: existing pymongo collection object
        :param db: existing pymongo db object
        """
        fn = '[common.mongo.MongoDB][__init__]'
        self.collection = collection_obj
        self.db = db_obj
        collection_name = collection; del collection  # -- to avoid ambiguity
        db_name = db; del db  # -- to avoid ambiguity
        self.client = db_client if db_client else None
        self.connected = False

        # -- validate passing objects
        if db_obj is not None and isinstance(db_obj, Database):
            self.client = db_obj.client
        if db_obj is not None and not isinstance(db_obj, Database):
            log.error(f"{fn} : db_obj: {type(db_obj)} is not a Database object")
            return
        if collection_obj is not None and not isinstance(collection_obj, Collection):
            log.error(f"{fn} : collection_obj: {type(collection_obj)} is not a Collection object")
            return

        # -- database basic config
        if db_config is None and self.db is None and self.collection is None:
            if os.environ.get('APP_RUNTIME_CONTEXT') == 'dev':
                db_config = config['mongo.dev'] if config['mongo.dev'] else config['mongodb']
                self.environ = 'dev'
            elif os.environ.get('APP_RUNTIME_CONTEXT') == 'qa':
                db_config = config['mongo.qa'] if config['mongo.qa'] else config['mongodb']
                self.environ = 'qa'
            else:
                db_config = config['mongo.prod']  if config['mongo.prod'] else config['mongodb']
                self.environ = 'prod'
            log.info(f"{fn} : Using mongo.{self.environ} configuration.")
        else:
            if db_config:
                log.info(f"{fn} : Using provided db_config: {db_config}")

        if db_config:
            db_name = db_config['database']
            self.client = MongoClient(
                f"mongodb://{db_config['host']}:{db_config['port']}/",
                connect=False,
                username=db_config['username'],
                password=db_config['password'],
                authSource=db_config['authenticationDatabase'])

        # -- setup database
        if not db_name and self.db is None:
            if db_config.get('database'):
                self.db = self.client[db_config['database']]
            else:
                self.db = self.client['test_db']
        elif db_name and not self.db:
            self.db = self.client[db_name]

        # -- setup collection
        if not collection_name and self.db is not None:
            if db_config and db_config.get('collection'):
                self.collection = self.db[db_config['collection']]
            elif self.collection is None:
                self.collection = self.db['test']
        elif collection_name and self.db is not None:
            self.collection = self.db[collection_name]

        if collection_obj is not None and db_obj is not None:
            log.info(f"{fn} : Using existing connection: {self.db.name}@{self.client.address}")
        else:
            log.info(f"{fn} : Connection object created for {self.db.name}")


    def close(self):
        fn = '[common.mongo.MongoDB][close]'
        if self.status():
            self.client.close()
            self.connected = False
            log.info(f"{fn} : DISCONNECTED.")

    def status(self):
        fn = '[common.mongo.MongoDB][status]'
        r = False
        try:
            if self.client and self.client.server_info():
                if isinstance(self.db.name, str):
                    r = True
            if r:
                log.info(f"{fn} : [CONNECTED] Using existing connection: {self.db.name}@{self.client.address}")
            else:
                log.info(f"{fn} : NOT CONNECTED.")
        except ServerSelectionTimeoutError:
            log.error(f"{fn} : Exception occured while using database object.")
        self.connected = r
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
        fn = '[common.mongo.MongoCRUD][cd]'
        if collection and self.connector.status():
            if db:
                self.collection = self.connector.db.client[db][collection]
                log.info(f"{fn} : Using database: {self.connector.db.name}")
                log.info(f"{fn} : and collection: {self.connector.db.name}.{self.collection.name}")
            else:
                self.collection = self.connector.db[collection]
                log.info(f"{fn} : Using collection: {self.connector.db.name}.{self.collection.name}")


    def create(self, doc=None, collection=None, db=None, add_ts=True):
        """
        Insert objects.
        :param doc: data to be inserted.
        :param collection: to change collection/table
        :param db: to change database
        """
        fn = '[common.mongo.MongoCRUD][create]'
        log.debug(f"{fn} : {doc}")
        self.cd(collection, db)
        count = 0
        r = None
        c = 204
        m = 'Nothing happened.'

        data = deepcopy(doc)
        try:
            ins = None
            data = self._encode_objectid(data)
            if isinstance(data, dict):
                if add_ts:
                    data['updated_dt'] = ts()
                ins = self.collection.insert_one(data)
                r = self._decode_objectid(ins.inserted_id)
                count = 1 if r else 0
            elif isinstance(data, list):
                for d in data:
                    if isinstance(d, dict) and add_ts:
                        d['updated_dt'] = ts()
                ins = self.collection.insert_many(data)
                r = ins.inserted_ids
                count = len(r)
            if r and ins:
                c = 200
                m = 'Data inserted.'
                log.info(f"{fn} : create_count: {count}, create_ack: {ins.acknowledged}")
        except Exception as e:
            c = 500
            m = 'create(): Server Error: {}'.format(e)
            log.error(f"{fn} : {m}")
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
        fn = '[common.mongo.MongoCRUD][read]'
        self.cd(collection, db)
        r = None
        c = 404
        m = 'No data returned.'
        doc_count = 0
        statement = []

        try:
            # -- build statement
            if where:
                where = self._encode_objectid(where)
                for k in where:
                    if where[k] is None:
                        statement += [(k, {'$exists': False})]
                    else:
                        statement += [(k, where[k])]
            else:
                statement += [('_id', {'$exists': True})]

            # if isinstance(aggr_cols, list):
            #     if isinstance(aggr_type, dict):
            #         pass  # sum
            #     else:
            #         pass  # count

            log.info(f"{fn} : retrieving docs like: {dict(statement)}" \
                     f"{f', {projection}' if projection else ''}")

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
            log.info(f"{fn} : read_count: {doc_count}")

        except Exception as e:
            # r = statement
            c = 500
            m = f"{fn} : Server Error: {e}"
            log.error(f"{fn} : {m}")
        return self._response(r, c, m)

    def read1(self, where=None, collection=None, db=None, projection=None, sort=None, aggr_cols=None, aggr_type=None, like=None):
        r = {}
        data = self.read(where, collection, db, projection, sort, aggr_cols, aggr_type, like)['data']
        if data:
            r = self._decode_objectid(data[0])
        return r

    def update(self, doc=None, collection=None, db=None, where=None, like=None, set=None, with_sync_id=False, add_ts=True):
        """
        :param doc: new version of database object to update
        :param collection: to change collection/table
        :param db: to change database
        :param where: criteria to locate database object i.e {'city': 'Atlanta}
        :param like: use filter with $regex i.e. like={'employe_name': '^Ran'}
        :param set: use $set to update field i.e. where={'_id': '5e1ab71ed4a0e6a7bdd5233f'}, set={'employe_name': 'Randoll'}
        :param with_sync_id: set True to enforce the right user is updating the right version of doc (credit: T. J. Killian)
        """
        fn = '[common.mongo.MongoCRUD][update]'
        log.debug(f"{fn} : update: {doc}")
        self.cd(collection, db)
        r = []
        c = 204
        m = 'Nothing happened.'

        verifier = None
        data = deepcopy(doc)
        try:
            if isinstance(data, dict):
                data = self._encode_objectid(data)
                if add_ts:
                    data['updated_dt'] = ts()

                if with_sync_id:
                    verifier = self.read1({
                        '_id': data['_id'],
                        '$or': [
                            {'_sync_id': data.get('_sync_id')},
                            {'_sync_id': {'$exists': False}},
                            {'_sync_id': {'$eq': None}},
                        ]
                    }, collection)
                    if verifier:
                        data['_sync_id'] = self._get_sync_id()
                        res = self.collection.replace_one({'_id': data['_id']}, data)
                        if res.modified_count:
                            c = 200
                            m = 'Documents updated. ({})'.format(data['_sync_id'])
                            r += [{'_sync_id': data['_sync_id']}]
                        else:
                            m = 'Document was found but not modified.'
                    else:
                        m += ' Document has wrong _sync_id.'
                        return self._response(r, c, m)
                else:
                    res = self.collection.replace_one({'_id': data['_id']}, data)
                    if res.modified_count:
                        c = 200
                        m = 'Documents updated.'
                    else:
                        m = 'Document was found but not modified.'

                    log.info(f"{fn} : " \
                             f"update_match_count: {res.matched_count}, " \
                             f"update_mod: {res.modified_count}, " \
                             f"update_ack: {res.acknowledged}")
        except Exception as e:
            r = data; del data
            c = 500
            m = f"{fn} : Server Error: {e}'"
            log.error(f"{fn} : {m}")
        return self._response(r, c, m)

    def delete(self, where=None, collection=None, db=None, truncate=False):
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
        fn = '[common.mongo.MongoCRUD][delete]'
        self.cd(collection, db)
        r = []
        c = 204
        m = 'Nothing happened.'

        log.debug(f"{fn} : 'delete docs like: {where}'")
        try:
            if truncate and not where:
                where = self.read({}, collection, projection={'_id': True})['data']
                log.info(f"{fn} : {collection} is set to be truncated.")
            else:
                m += " Criteria/parameters are missing."

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
                        log.info(f"{fn} : 'delete_count: {obj.deleted_count}, " \
                                 f"delete_ack: {obj.acknowledged}'")
                        r += [{'statement': self._decode_objectid(s), 'delete_count': obj.deleted_count, 'delete_ack':obj.acknowledged}]
                c = 200
                m = 'Items deletion have been executed.'
        except Exception as e:
            r = where
            c = 500
            m = f"{fn} : Server Error: {e}"
            log.error(f"{fn} : {m}")
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
        r = deepcopy(o)

        def _convert(_objects):
            _i = 0
            _r = _objects.copy()
            for _o in _objects:
                try:
                    _r[_i]['_id'] = ObjectId(_o['_id'])
                except:
                    try:
                        _r[_i]['_id'] = int(_o['_id'])
                    except:
                        pass
                _i += 1
            return _r

        if isinstance(o, dict):
            r = _convert([o])[0]
        elif isinstance(o, list):
            r = _convert(o)
        return r

    def _get_sync_id(self):
        return str(uuid4())

    def _response(self, data=None, rcode=None, message=None):
        fn = '[common.mongo.MongoCRUD][_response]'
        r = {'status': {'code': None, 'message': None}, 'data': []}

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

        r['status'] = {'code': rcode, 'message': message, 'docs': len(r['data'])}
        log.debug(f"{fn} : {r}")
        return r


db = MongoDB()
dao = MongoCRUD(collection_obj=db.collection, db_obj=db.db)
