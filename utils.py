__author__ = 'vseklecov'

import configparser
import inspect
import os

PY_PATH = os.path.split(os.path.abspath(inspect.getsourcefile(lambda _: None)))[0]


class CfgReader:

    def __init__(self, filename=os.path.join(PY_PATH, 'conf', 'sopds.conf')):
        config = configparser.ConfigParser()
        config.read(filename, 'utf-8')

        CFG_G = 'global'
        self.NAME = config.get(CFG_G, 'name', fallback='Simple OPDS Catalog')
        self.ROOT_URL = config.get(CFG_G, 'root_url', fallback='http://home/')
        self.PORT = config.get(CFG_G, 'port', fallback=8000)

        self.ENGINE = config.get(CFG_G, 'engine', fallback='sqlite:///')
        self.DB_NAME = config.get(CFG_G, 'db_name', fallback=os.path.join(PY_PATH, 'db', 'sopds.db'))
        self.DB_USER = config.get(CFG_G, 'db_user', fallback='sopds')
        self.DB_PASS = config.get(CFG_G, 'db_pass', fallback='sopds_pass')
        self.DB_HOST = config.get(CFG_G, 'db_host', fallback='localhost')
        self.DB_CHARSET = config.get(CFG_G, 'db_charset', fallback='utf-8')

        self.ROOT_LIB = os.path.abspath(config.get(CFG_G, 'root_lib', fallback=r'\documents\books'))
        self.FORMATS = config.get(CFG_G, 'formats', fallback='.pdf .djvu .fb2 .txt')
        self.DUBLICATES_FIND = config.getboolean(CFG_G, 'dublicates_find', fallback=True)
        self.DUBLICATES_SHOW = config.getboolean(CFG_G, 'dublicates_show', fallback=False)
        self.FB2PARSE = config.getboolean(CFG_G, 'fb2parse', fallback=True)
        self.ZIPSCAN = config.getboolean(CFG_G, 'zipscan', fallback=True)
        self.ZIPRESCAN = config.getboolean(CFG_G, 'ziprescan', fallback=False)
        self.COVER_EXTRACT = config.getboolean(CFG_G, 'cover_extract', fallback=False)

        self.FB2HSIZE = config.getint(CFG_G, 'fb2hsize', fallback=0)
        self.MAXITEMS = config.getint(CFG_G, 'maxitems', fallback=50)
        self.SPLITAUTHORS = config.getint(CFG_G, 'splitauthors', fallback=300)
        self.SPLITTITLES = config.getint(CFG_G, 'splittitles', fallback=300)
        self.COVER_SHOW = config.getint(CFG_G, 'cover_show', fallback=0)
        zip_codepage = config.get(CFG_G, 'zip_codepage', fallback='cp866')

        if self.COVER_EXTRACT:
            self.FB2SIZE = 0

        self.EXT_LIST = self.FORMATS.lower().split()

        if zip_codepage.lower() in {'cp437', 'cp866', 'cp1251', 'utf-8'}:
            self.ZIP_CODEPAGE = zip_codepage.lower()
        else:
            self.ZIP_CODEPAGE = 'cp437'

        CFG_S = 'site'
        self.SITE_ID = config.get(CFG_S, 'id', fallback='http://home/')
        self.SITE_TITLE = config.get(CFG_S, 'title', fallback='OPDS Catalog')
        self.SITE_ICON = config.get(CFG_S, 'icon', fallback='http://home/favicon.ico')
        self.SITE_AUTOR = config.get(CFG_S, 'autor', fallback='Victor')
        self.SITE_URL = config.get(CFG_S, 'url', fallback='http://home')
        self.SITE_EMAIL = config.get(CFG_S, 'email', fallback='victor@home')
        self.SITE_MAINTITLE = config.get(CFG_S, 'main_title', fallback='Root of Simple OPDS Catalog')

