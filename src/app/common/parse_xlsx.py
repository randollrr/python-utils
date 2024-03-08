from datetime import datetime
import json

import pandas as pd

from common.utils import deprecated, log
from common.mongo import dao

__version__ = '0.2.4'


class XlsxDataCollector:

    def __init__(self, filename, sheetname=None, transformer=None, auto_parse=True):
        self.data = []
        self.filename = filename
        self.xls_file = None
        self.sheetname = sheetname
        self.transformer = transformer if isinstance(transformer, dict) else None

        # -- read file and parse
        if auto_parse:
            self.read_file()
            self.read_sheet()
            self.parse()
        return

    # def __new__(cls, filename, sheetname=None, transformer=None):
    #     cls.__init__(filename, sheetname, transformer)
    #     return cls.get_data()

    def get_data(self):
        return self.data

    def read_file(self, filename=None):
        fn = '[common.parse_xlsx][read_file]'

        if filename:
            self.filename = filename
        try:
            self.xls_file = pd.ExcelFile(self.filename)
        except Exception as e:
            log.error(f"{fn} : File type error, Excel (xlsx) file is expected. \n{e}")

    def read_sheet(self, sheetname=None, sort_by=None, headers=0, ret='dict'):
        """Reads the sheet and returns the data as a list of dict."""
        fn = '[common.parse_xlsx][read_sheet]'
        r = None

        log.info(f'{fn} : Reading sheet: {sheetname}...')

        if not sheetname and not self.sheetname:
            self.sheetname = 0
        elif sheetname:
            self.sheetname = sheetname

        try:
            list_cols = None
            if self.transformer:
                list_cols = self.transformer.keys()
            df = pd.read_excel(
                self.xls_file,
                sheet_name=self.sheetname,
                usecols=list_cols,
                header=headers)
            if sort_by:
                df = df.sort_values(by=sort_by)
            data = df.fillna('').to_dict('records')

            self.data = []
            for d in data:
                t_rec = {}
                for k in d:
                    if self.transformer:
                        t_rec.update({self.transformer[k]: d[k]})
                    else:
                        t_rec.update({k: d[k]})
                self.data += [t_rec]
            r = df if ret == 'df' else self.data
            del df, data
        except Exception as e:
            self.data = []
            log.error(f"{fn} : Parsing issues (w/ Pandas) encountered.\n {e}")
        return r

    def parse(self):
        pass

    @deprecated
    def save2db(self, data=None, collection=None, truncate=False, where={}):
        """Deprecated: for a more conventional function name."""
        return self.save_to_db(data=data, collection=collection,
                               truncate=truncate, where=where)

    def save_to_db(self, data=None, collection=None, truncate=False, where={}):
        fn = '[common.parse_xlsx][save_to_db]'
        r = None

        log.info(f'{fn} Saving data to db...')

        if not data:
            data = self.data
        if not collection:
            collection = 'parsed_xlsx_data'
        if data:
            if truncate:
                dao.delete(
                    dao.read(where=where, collection=collection)['data'],
                    collection=collection)
            r = dao.create(data, collection)
        return r

    def to_date(self, dt):
        r = dt
        try:
            r = datetime.strftime(datetime.strptime(dt, '%m/%d/%Y'), '%Y-%m-%d')
        except:
            try:
                r = datetime.strftime(datetime.strptime(dt.replace('PST', '')
                        .replace('PDT', '')
                        .replace('\t', '')
                        .strip(),
                        '%b %d, %Y'),
                    '%Y-%m-%d')
            except:
                pass
        return r

    def to_dict(self):
        return self.data

    def to_json(self):
        r = None
        if self.data:
            r = json.dumps(self.data)
        return r


# CHANGELOG
# v0.1.0 Initial implementation
# v0.2.0 optimized read_sheet():
# - support no transformers
# - support headers w/ multi-row or start row other than zero
# v0.2.1 added support for auto_parse=true|false in constructor (default: True)
# v0.2.2 added support for read_sheet() to return parsed dict or the df (DataFrame)
# v0.2.3 bugfix: return var used before assigned
# v0.2.4 optimized read_sheet() and read_file()
