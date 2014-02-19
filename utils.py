__author__ = 'vseklecov'

import base64
import configparser
import datetime
import inspect
import mimetypes
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
        self.COVER_PATH = os.path.abspath(config.get(CFG_G, 'cover_path', fallback=r'\documents\covers'))
        self.FORMATS = config.get(CFG_G, 'formats', fallback='.pdf .djvu .fb2 .txt')
        self.DUBLICATES_FIND = config.getboolean(CFG_G, 'dublicates_find', fallback=True)
        self.DUBLICATES_SHOW = config.getboolean(CFG_G, 'dublicates_show', fallback=False)
        self.FB2PARSE = config.getboolean(CFG_G, 'fb2parse', fallback=True)
        self.ZIPSCAN = config.getboolean(CFG_G, 'zipscan', fallback=True)
        self.ZIPRESCAN = config.getboolean(CFG_G, 'ziprescan', fallback=False)
        self.COVER_EXTRACT = config.getboolean(CFG_G, 'cover_extract', fallback=False)
        self.LAST_SCAN = config.get(CFG_G, 'last_scan', fallback=datetime.date.today())

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



class Author:
    def __init__(self, author):
        ns = self.author.tag.split('}')[0][1:]
        last_name = author.findtext(ET.QName(ns, 'last-name').text, '').strip(' \'\"\&()-.#[]\\\`')
        first_name = author.findtext(ET.QName(ns, 'first-name').text, '').strip(' \'\"\&()-.#[]\\\`')
        nickname = author.findtext(ET.QName(ns, 'nickname').text, '').strip(' \'\"\&()-.#[]\\\`')
        if (len(last_name) + len(first_name)) == 0:
            self.last_name = nickname
        else:
            self.first_name = first_name
            self.last_name = last_name


class Image:
    def __init__(self, root, image):
        _id = image.get('{http://www.w3.org/1999/xlink}href')
        if _id[0] == '#':
            binary = root.find("*/[@id='{:s}']".format(_id[1:]))
            if binary:
                self.content_type = binary.get('content-type').lower()
                self.image = base64.b64decode(binary.text)
        else:
            self.content_type = ''


class FictionBook:

    def __init__(self, filename):
        if isinstance(filename, str):
            if os.path.exists(filename):
                try:
                    self.tree = ET.parse(filename)
                    self.parsed = True
                except ET.ParseError:
                    self.parsed = False
            else:
                self.parsed = False
        elif hasattr(filename, 'read'):
            try:
                self.tree = ET.fromstring(filename.read())
                self.parsed = True
            except ET.ParseError:
                self.parsed = False
        else:
            self.parsed = False
        if self.parsed:
            self.root = self.tree.getroot()
            ns = self.root.tag.split('}')[0][1:]
            desc = self.root.find(ET.QName(ns, 'description').text)
            ti = desc.find(ET.QName(ns, 'title-info').text)
            self.genres = []
            for genre in ti.iter(ET.QName(ns, 'genre').text):
                self.genres.append(genre.text.lower().strip(' \'\"\&()-.#[]\\\`'))
            self.authors = [Author(author) for author in ti.iter(ET.QName(ns, 'author').text)]
            self.lang = ti.findtext(ET.QName(ns, 'lang').text, 'ru').strip(' \'\"')
            self.title = ti.findtext(ET.QName(ns, 'book-title').text, '').strip(' \'\"\&()-.#[]\\\`')
            self.annotation = ET.tostring(ti.findtext(ET.QName(ns, 'annotation').text, ''), 'unicode', 'text')
            coverpage = ti.find(ET.QName(ns, 'coverpage').text)
            if coverpage:
                image = coverpage.find(ET.QName(ns, 'image').text)
                if image:
                    self.cover = Image(self.root, image)
            sequence = ti.find(ET.QName(ns, 'sequence').text)
            if sequence:
                self.name_sequence = sequence.get('name')
                self.number_in_seq = sequence.get('number')
            else:
                self.name_sequence = ''


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
        (n, ext) = os.path.splitext(name)
        if ext.lower() == '.fb2' and cfg.FB2PARSE:
            fb = FictionBook(filename)
            book_id = dbase.addbook(name, rel_path, cat_id, ext, fb.title, fb.lang, file_size, archive,
                                    cfg.DUBLICATES_FIND, fb.annotation)
            for author in fb.authors:
                author_id = dbase.addauthor(author.first_name, author.last_name)
                dbase.addbauthor(book_id, author_id)
            for genre in fb.genres:
                dbase.addbgenre(book_id, dbase.addgenre(genre))
            if cfg.COVER_EXTRACT:
                ext = mimetypes.guess_extension(fb.cover.content_type)
                if ext:
                    fn = str(book_id) + ext
                    fp = os.path.join(cfg.COVER_PATH, fn)
                    img = open(fp, 'wb')
                    img.write(fb.cover.image)
                    img.close()
                    dbase.addcover(book_id, fn, fb.cover.content_type)


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
        if not os.path.isdir(cfg.COVER_PATH):
            os.mkdir(cfg.COVER_PATH)

    ext_set = {x for x in cfg.EXT_LIST}
    if args.verbose:
        print(ext_set)

    if args.scan_all:
        for full_path, dirs, files in os.walk(cfg.ROOT_LIB):
            for name in files:
                fn = os.path.join(full_path, name)
                (n, ext) = os.path.splitext(name)
                if ext.lower() == '.zip' and cfg.ZIPSCAN:
                    if args.verbose:
                        print('Add file: {:s}'.format(full_path))
                    processzip(dbase, name, full_path, fn)
                elif ext.lower() in ext_set:
                    if args.verbose:
                        print('Add file: {:s}'.format(full_path))
                    processfile(dbase, name, full_path, fn, cfg)

    dbase.close_db()
