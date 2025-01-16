# python-utils
- common.utils
- common.mongo
- common.fm
<br><br>


## common.utils.py

### 1.22.0
- add do_get() and _do_request()

### 1.21.0
- add change_to to config.file_type()

### 1.18
- add `ts()`, returns ISO formatted UTC (now) -- non-ISO date, str-based or actual object
- add `rwjson()`, to read/write json data to the filesystem seemlessly

### 1.17
- add `next_add(<str>)`, return value +1 from string based numbers

### 1.16
- add `status` object

### 1.15
- remove support for email (REST-based service will be used instead)

### 1.14
- re-write email support (using smtplib)

### 1.13
### 1.12

### 1.11
- add missing initialization to `log.log_filename` and made private (log._log_filename)

### 1.10
- show logging on screen only
- improve `log.gethandler()`

### 1.9
- add `log.reset()`

### 1.8
- add support to not save but display a log is ok

### 1.7
- remove all python 3.7 string formating

### 1.6
- optimize `Config()`, make it more flexible to read, write yaml/json file
- add `Config.set()`, to set a new configuartion file
- add `Log.config()`, to set a new log configuartion
- optimize `Log()`, added support for on-screen logging toggle
- remove `Database()`
- change params access type
- add generic config object to be imported

### [backlog]
- add `status.from_dict(status)`
- add `status.from_json(status)`
<br><br>


## common.mongo.py

### 1.4.1
- fix issues with _sync_id being null

### 1.4.0
- add timestamp updated_dt by default (param: add_ts=True)

### 1.3.5
- add with_sync_id feature to update() to a randomly generated _sync_id to docs

### 1.3.1
- 2nd update, keeping same version: bugfix with db_name when using `db_config`
- added support `MongoClient` (`db_client`) connection spawning
- modified connection creation got sub-process/thread forks

### 1.3.0
- bugfix with db_name when using `db_config`
- fixed `read1()` with encoding/decoding `object_id`
- optimized `_encode_objectid()`
- issues with pymongo db/collection objects no longer "implement truth value testing or bool()"
- change `delete()` positive confirmation return value to 200 (from 410)

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

### [backlog]
- add aggregation to MongoCRUD.read()
<br><br>


## common.fm.py

### 2.5.0
- updated strings to f-string
- added fm.fullpath, fm.cd(<relative-path>), fm.pwd()
- add support to fm.ls() to return file/dir object w/ better details
- add support to create/delete subfolders
- added common.create feature to dir_struct() and set_bucket()
- added override=True to fm.move() to not add +1 to filename if exists at destination
- updated logging

### 2.4.2
- remove conditional general path update
- bugfix: fm.ls() returning fn_only (filname only)

### 2.4.1
- ???

### 2.4.0
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
<br><br>


## common.scheduler

### 1.2.0
- implement imported module reload
- other minor updates: formatting, logging, function-renaming

### 1.1.2
- bugfix: with parsing arguments per cron + protect cron config read

### 1.1.1
- updated logging messages

### 1.1.0
- add support for parameters to scheduler.run_job([params={}])
- add support for new crontab schema
- add support for return status (JSON) from running jobs

### 1.0.1
...

### 1.0.0
- initial implementation


## common.parse_xlsx

### v0.3.2
- updated logging in read_sheet()

### v0.3.1
- added support for skiprows in read_sheet()

### v0.3.0
- added support to switch between openpyxl (.xlsx) and xlrd (.xls) engines

### v0.2.4
- optimized read_sheet() and read_file()

### v0.2.3
- bugfix: return var used before assigned

### v0.2.2
- added support for read_sheet() to return parsed dict or the df (DataFrame)

### v0.2.1
- added support for auto_parse=true|false in constructor (default: True)

### v0.2.0
- optimized read_sheet():
- support no transformers
- support headers w/ multi-row or start row other than zero

### v0.1.0
- Initial implementation
