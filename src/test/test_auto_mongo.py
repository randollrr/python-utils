import json

import pytest

from auto_mongo import db, dao, MongoDB, MongoCRUD
from auto_utils import log

log.reset()
object_ids = {}


def test_create():
    assert dao.create({'_id': 'randollrr', 'name': 'Randoll Revers', 'gender': 'M', 'age': None})

    obj1 = dao.create([{'1': 2}, {'a': 'b, c'}])
    assert obj1['data']

    obj2 = dao.create({'hello': [{'world': 1}, {'haiti': {'pv': 'access_ht'}}, {'me': 'and my...'}]})
    assert obj2['data']

    # ref: https://docs.mongodb.com/v3.2/tutorial/query-documents/
    data = [{'_id': 1,
             'name': 'sue',
             'age': 19,
             'type': 1,
             'status': 'P',
             'favorites': { 'artist': 'Picasso', 'food': 'pizza' },
             'finished': [ 17, 3 ],
             'badges': [ 'blue', 'black' ],
             'points': [ { 'points': 85, 'bonus': 20 }, { 'points': 85, 'bonus': 10 } ]},
            {'_id': 4,
             'name': 'xi',
             'age': 34,
             'type': 2,
             'status': 'D',
             'favorites': { 'artist': 'Chagall', 'food': 'chocolate' },
             'finished': [ 5, 11 ],
             'badges': [ 'red', 'black' ],
             'points': [ { 'points': 53, 'bonus': 15 }, { 'points': 51, 'bonus': 15 } ]},
            {'_id': 6,
             'name': 'abc',
             'age': 43,
             'type': 1,
             'status': 'A',
             'favorites': { 'food': 'pizza', 'artist': 'Picasso' },
             'finished': [ 18, 12 ],
             'badges': [ 'black', 'blue' ],
             'points': [ { 'points': 78, 'bonus': 8 }, { 'points': 57, 'bonus': 7 } ]}]
    ids = dao.create(data)
    assert ids['data']

    object_ids['delete_list'] = ids['data'] + obj1['data'] + obj2['data']


def test_read():
    dao.cd('test')
    assert dao.read()['status']['code'] == 200
    assert dao.read({})['status']['code'] == 200
    assert dao.read({'_test': '_test'})['status']['code'] == 404
    assert dao.read({}, sort={'_id': -1})['status']['code'] == 200

# @pytest.mark.skip
def test_projection():
    data = dao.read(
        where={'_id': 1},
        collection='test',
        projection={'_id': False, 'name': True, 'type': True, 'status': True})['data'][0]

    print(list(data.keys()))
    assert list(data.keys()) == ['name', 'type', 'status']


def test_update():
    data = dao.read({'_id': 4})['data'][0]
    for d in data['points']:
        if d['points'] == 51:
            d['bonus'] = 888
    dao.update(data)
    data = dao.read({})['data']
    for d in data:
        d['vendor'] = 'my-company'
        dao.update(d)


def test_update_with_sync_id():
    dao.create({'vendor': 'my-company'}, 'test')
    data = dao.read1({'vendor': 'my-company'}, 'test')
    assert dao.update(data, with_sync_id=True)['status']['code'] == 200
    data['_sync_id'] = '8bd9cf50-acc8-42e8-8736-13102e54efa4'  # some previous value
    assert dao.update(data, with_sync_id=True)['status']['code'] == 204
    data['_sync_id'] = ''
    assert dao.update(data, with_sync_id=True)['status']['code'] == 204
    del data['_sync_id']
    assert dao.update(data, with_sync_id=True)['status']['code'] == 204
    data = dao.read1({'vendor': 'my-company'}, 'test')
    data['updated_dt'] = 'today-is-the-day'
    assert dao.update(data, with_sync_id=True)['status']['code'] == 200


def test_delete():
    assert dao.delete({})['status']['code'] == 204
    if object_ids.get('delete_list'):
        assert dao.delete(object_ids['delete_list'])
    assert dao.delete({'_id': 'randollrr'})


# @pytest.fixture
# def test_teardown(dbms):
def test_teardown_test():
    # dbo = dbms['db']
    # dbo.drop_collection('test')
    # dbo.client.drop_database('test_db')
    dao.delete(dao.read({}, 'test')['data'], 'test')


def test_connection():
    dao.connector.status()
    assert db.status()
    assert dao.connector.connected
    assert MongoDB(collection_obj=dao.collection, db_obj=dao.connector.db).status()
    assert MongoDB(db_obj=dao.connector.db).status()
    assert not MongoDB(collection_obj='invalid value', db_obj='invalid value').status()
    dao.connector.close()
    assert not dao.connector.connected
    # assert not db.status()  # can no longer use db after closing connection
    # db.connect()            # as of MongoDB 4.2.2+
    # assert dao.connector.connected
