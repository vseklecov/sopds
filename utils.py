__author__ = 'vseklecov'

import configparser
import inspect
import os
import xml.etree.ElementTree as ET

import db as opdsdb

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


def fb2parse(filename):
    book = opdsdb.Book()
    if isinstance(filename, str):
        tree = ET.parse(filename)
    else:
        tree = ET.fromstring(filename.read())
    root = tree.getroot()
    ns = root.tag.split('}')[0][1:]

    description = root.find(ET.QName(ns, 'description').text)
    title_info = description.find(ET.QName(ns, 'title-info').text)
    for genre in title_info.iter(ET.QName(ns, 'genre').text):
        book.genres.append(opdsdb.addgenre(genre.text))

    for author in title_info.iter(ET.QName(ns, 'author').text):
        last_name = author.findtext(ET.QName(ns, 'last-name').text, '')
        first_name = author.findtext(ET.QName(ns, 'first-name').text, '')
        book.authors.append(opdsdb.addauthor(first_name, last_name))

    book.lang = title_info.findtext(ET.QName(ns, 'lang').text, 'ru')
    book.title = title_info.findtext(ET.QName(ns, 'book-title').text, '')
    ret['cover_name'] = ''
    ret['cover_image'] = ''

    return book


def processzip(dbase, name, full_path, filename):
    pass


def processfile(dbase, name, full_path, filename, cfg, archive=0, file_size=0, cat_id=0):
    rel_path = os.path.relpath(full_path, cfg.ROOT_LIB)
    if dbase.findbook(name, rel_path) == 0:
        if archive == 0:
            cat_id = dbase.addcattree(rel_path, archive)
        title = ''
        lang = ''
        (n, e) = os.path.splitext(name)
        if e.lower() == '.fb2' and cfg.FB2PARSE:
            book = fb2parse(filename)
            lang = book['lang'].strip(' \'\"')
            title = book['book_title'].strip(' \'\"\&()-.#[]\\\`')
            book_id = dbase.addbook(name, rel_path, cat_id, e, title, lang, file_size, archive, cfg.DUBLICATES_FIND)

            for author in book['authors']:
                last_name = author['last_name'].strip(' \'\"\&()-.#[]\\\`')
                first_name = author['first_name'].strip(' \'\"\&()-.#[]\\\`')
                author_id = dbase.addauthor(first_name, last_name)
                dbase.addbauthor(book_id, author_id)

            for genre in book['genres']:
                dbase.addbgenre(book_id, dbase.addgenre(genre.lower().strip(' \'\"\&()-.#[]\\\`')))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Simple OPDS Scaner - program for scan your e-book directory and store data to database.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-s', '--scan-all', help='Full rescan all library', action='store_true')
    group.add_argument('-l', '--last', help='Scan files from date after last scan', action='store_false')
    parser.add_argument('-v', '--verbose', help='Enable verbose output', action='store_true')
    parser.add_argument('-c', '--config', help='Config file path')

    args = parser.parse_args()

    if args.verbose:
        print('Option set: scan-all = %s, scan-last = %s, config path = %s' % (args.scan_all, args.last, args.config))

    if args.config and os.path.isfile(args.config):
        cfg = CfgReader(args.config)
    else:
        cfg = CfgReader()

    dbase = opdsdb.opdsDatabase(cfg.ENGINE+cfg.DB_NAME, cfg.DB_USER, cfg.DB_PASS, cfg.DB_HOST, cfg.ROOT_LIB)
    dbase.open_db()

    if args.verbose:
        print(dbase.print_db_err())

    if cfg.COVER_EXTRACT:
        if not os.path.isdir(os.path.join(PY_PATH,'covers')):
            os.mkdir(os.path.join(PY_PATH,'covers'))

    ext_set = {x for x in cfg.EXT_LIST}
    if args.verbose:
        print(ext_set)

    for full_path, dirs, files in os.walk(cfg.ROOT_LIB):
        for name in files:
            fn = os.path.join(full_path, name)
            (n, e) = os.path.splitext(name)
            if e.lower() == '.zip' and cfg.ZIPSCAN:
                processzip(dbase, name, full_path, fn)
            elif e.lower() in ext_set:
                processfile(dbase, name, full_path, fn, cfg)
    dbase.close_db()
