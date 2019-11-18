# auto_utils.py

## 1.7 
- removed python 3.7 string formating

## 1.6 
- optimized Config(), make it more flexible to read, write yaml/json file
- added Config.set(), to set a new configuartion file
- added Log.config(), to set a new log configuartion
- optimized Log(), added support for on-screen logging toggle
- removed Database()
- changed params access type
- added generic config object to be imported


# auto_fm.py

## 2.2 
- removed python 3.7 string formating
- renamed delete_files() --> del_files()
- added retainer(): to apply rentention policies
- added touch(), mimicking touch from the CLI

## 2.1 
- fixed path isssue in delete() by adding os.path.join()

## 2.0 optimized move.do_move()
- added now return file ts in latest()
- ported dir_struct() from mongobak.py
- optimized latest() --> ts_sorted_file()
- added oldest()
- added delete() --> delete_files()
