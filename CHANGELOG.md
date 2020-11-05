# python-utils
- auto_utils
- auto_mongo
- auto_fm


## auto_utils.py
---

### 1.11
- added missing initialization to log.log_filename and made private (log._log_filename)

### 1.10
- show logging on screen only
- improved log.gethandler()

### 1.9
- added log.reset()

### 1.8
- added support to not save but display a log is ok

### 1.7 
- removed all python 3.7 string formating

### 1.6 
- optimized Config(), make it more flexible to read, write yaml/json file
- added Config.set(), to set a new configuartion file
- added Log.config(), to set a new log configuartion
- optimized Log(), added support for on-screen logging toggle
- removed Database()
- changed params access type
- added generic config object to be imported


## auto_mongo.py 
---

[ ### 1.3 ]
[ - add aggregation to MongoCRUD.read() ]


### 1.2.3
- added support projections on read()


### 1.2.2
- fix issues w/ MongoDB constructor and to use `db` and `collection` object passed to it
- added support for `collection` and `db` objects initialization in MongoDB and MongoCRUD constructors


### 1.2
- added default dao and db objects to module
- renamed _update_session() to cd() to ease access
- cleaned INFO logging.

### 1.1.1
- added sort to MongoCRUB.read()
- changed _update_session() to log only if connected

### 1.0 
- MongoDB: easy connection
- MongoCRUD: basic CRUD functionalities


## auto_fm.py
---

### 2.2 
- removed python 3.7 string formating
- renamed delete_files() --> del_files()
- added retainer(): to apply rentention policies
- added touch(), mimicking touch from the CLI

### 2.1 
- fixed path isssue in delete() by adding os.path.join()

### 2.0 optimized move.do_move()
- added now return file ts in latest()
- ported dir_struct() from mongobak.py
- optimized latest() --> ts_sorted_file()
- added oldest()
- added delete() --> delete_files()

