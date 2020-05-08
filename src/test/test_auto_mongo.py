import json

import pytest

from auto_mongo import MongoDB
from auto_mongo import MongoCRUD
from auto_utils import config
from auto_utils import log

log.reset()
object_ids = {}

@pytest.fixture
def dbms():
    dao = MongoCRUD('test', 'test_db')
    db = dao.connector.db
    yield {'db': db, 'dao': dao}


def test_connection(dbms):
    db = MongoDB()
    assert db.status()
    assert not dbms['dao'].connector.close()

# @pytest.mark.skip
def test_create(dbms):
    assert dbms['dao'].create({'_id': 'randollrr', 'name': 'Randoll Revers', 'gender': 'M', 'age': None})
    
    obj1 = dbms['dao'].create([{'1': 2}, {'a': 'b, c'}])
    assert obj1['data']
    
    obj2 = dbms['dao'].create({'hello': [{'world': 1}, {'haiti': {'pv': 'access_ht'}}, {'me': 'and my...'}]})
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
    ids = dbms['dao'].create(data)
    assert ids['data']
    object_ids['delete_list'] = ids['data'] + obj1['data'] + obj2['data']


def test_read(dbms):
    assert dbms['dao'].read()['status']['code'] == 200
    assert dbms['dao'].read({'_test': '_test'})['status']['code'] == 404
    assert dbms['dao'].read({}, sort={'_id': -1})['status']['code'] == 200
    # assert dbms['dao'].read({}, projection={'_id': False})['status']['code'] == 200

# @pytest.mark.skip
def test_update(dbms):
    data = dbms['dao'].read({'_id': 4})['data'][0]
    for d in data['points']:
        if d['points'] == 51:
            d['bonus'] = 888
    dbms['dao'].update(data)


# @pytest.mark.skip
def test_delete(dbms):
    assert dbms['dao'].delete({})['status']['code'] == 204
    if object_ids.get('delete_list'):
        assert dbms['dao'].delete(object_ids['delete_list'])
    assert dbms['dao'].delete({'_id': 'randollrr'})


# @pytest.fixture
def test_teardown(dbms):
    dbo = dbms['db']
    dbo.drop_collection('test')
    dbo.client.drop_database('test_db')
