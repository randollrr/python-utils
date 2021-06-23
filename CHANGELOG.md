# python-utils
- auto_utils
- auto_mongo
- auto_fm


## auto_utils.py
---

### 1.11
- add missing initialization to log.log_filename and made private (log._log_filename)

### 1.10
- show logging on screen only
- improve log.gethandler()

### 1.9
- add log.reset()

### 1.8
- add support to not save but display a log is ok

### 1.7
- remove all python 3.7 string formating

### 1.6
- optimize Config(), make it more flexible to read, write yaml/json file
- add Config.set(), to set a new configuartion file
- add Log.config(), to set a new log configuartion
- optimize Log(), added support for on-screen logging toggle
- remove Database()
- change params access type
- add generic config object to be imported


## auto_mongo.py
---

[ ### 1.3 ]
[ - add aggregation to MongoCRUD.read() ]


### 1.2.3
- add support projections on read()


### 1.2.2
- fix issues w/ MongoDB constructor and to use `db` and `collection` object passed to it
- add support for `collection` and `db` objects initialization in MongoDB and MongoCRUD constructors


### 1.2
- add default dao and db objects to module
- rename _update_session() to cd() to ease access
- clean INFO logging.

### 1.1.1
- add sort to MongoCRUB.read()
- change _update_session() to log only if connected

### 1.0
- MongoDB: easy connection
- MongoCRUD: basic CRUD functionalities


## auto_fm.py
---

### 2.4
- change default directory generation to ['archive', 'errored', 'input', 'output']
- add flag fn_only to ls(), latest(), oldest()
- optimize dir_struct()
- add del_dir()
- add support for buckets, change to stateful for all funcions (no @staticmethod)

### 2.3.1
- bugfix: add return value to del_files()

### 2.3
- ???

### 2.2
- remove python 3.7 string formating
- rename delete_files() --> del_files()
- add retainer(): to apply rentention policies
- add touch(), mimicking touch from the CLI

### 2.1
- fix path isssue in delete() by adding os.path.join()

### 2.0 optimized move.do_move()
- add now return file ts in latest()
- port dir_struct() from mongobak.py
- optimize latest() --> ts_sorted_file()
- add oldest()
- add delete() --> delete_files()

