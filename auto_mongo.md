# auto_mongo

A typical CRUD library for mongoDB that can be useful for most projects, but initial from my home automation project -- built on top of pymongo.

To use this library all you need to do is to import it from your directory path.

```python
from auto_mongo import MongoCRUD

dao = MongoCRUD()  # all config.json parameters will be used
dao = MongoCRUD('collection_name', 'database_name')  # or override collection and database parameters
```

Note: `auto_mongo.py` currently has `auto_utils.py` as a dependency.

<br>

## CRUD Functions

### Create

To create a new record of document inside a collection in the mongodb database, it' s as simple as:

```python
res = dao.create({'new': 'data'})
res = dao.create(doc={'new': 'data'}, collection='collection_name', db='db_name')
```

### Read

To read data from the database, all you need to do is as follow:

```python
data = dao.read({})
data = dao.read(where={}, 'collection_name')
data = dao.read({}, 'collection_name', 'db_name')
data = dao.read(where={'_id': 1}, collection='collection_name', db='db_name')
data = dao.read({}, projection={'_id': False, 'field_name': True}, sort={'field_name1': -1, 'field_name2': 1})
```

You get the gist.


### Update

Update one document at a time.

```python
res = dao.update({'_id': '<object_id>', 'new': 'data'})
res = dao.update(doc={'_id': '<object_id>', 'new': 'data'}, collection='collection_name', db='db_name')
```

### Delete

Delete one document or multiple documents at once.

```python
res = dao.delete(where={'_id': '<object_id>'}, collection='collection_name', db='db_name')
res = dao.delete([{'_id': '<object_id>'}, {'_id': '<object_id>', 'field_name': 'value'}])
res = dao.delete(where=['<object_id1>', '<object_id2>', '<object_id3>', ])
```

> <b><u>Note</u></b>: The `dao` object will always keep state from the function that was called last. Use `dao.cd('collection_name')` to switch collection or `dao.cd('collection_name', 'database_name')` to switch collection and database.

<br><br>

## Configuration

A `config.json` file is required with the following minimal parameters:

```json
{
  "service": {
    "app-name": "app",
    "app-logs": null,
    "log-level": "DEBUG",
    "log-stdout": true
  },
  "mongo.dev": {
    "username": null,
    "password": null,
    "host": "localhost",
    "port": 27017,
    "database": "test_db",
    "collection": "test",
    "authenticationDatabase": "test_db"
  },
  "mongo.prod": {
    "username": "username",
    "password": "password",
    "host": "db.host.domain",
    "port": 27017,
    "database": "prod_db",
    "authenticationDatabase": "prod_db"
  }
}

```

> <b><u>Note</u></b>: Parameter `"collection": <collection_name>` can be omitted in this config file. And `APP_RUNTIME_CONTEXT` environment variable can be set to `dev` to enable `mongo.dev`, `qa` for `mongo.qa` and `prod` for the `mongo.prod` section -- `prod` is also assumed by default.

