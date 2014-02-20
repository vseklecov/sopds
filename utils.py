__author__ = 'vseklecov'

import base64
import configparser
import inspect
import mimetypes
import os
import PIL.Image
import time
import xml.etree.ElementTree as ET
import zipfile

import db as opdsdb

PY_PATH = os.path.split(os.path.abspath(inspect.getsourcefile(lambda _: None)))[0]
VERBOSE = False

class CfgReader:

    CFG_G = 'global'

    def __init__(self, filename=os.path.join(PY_PATH, 'conf', 'sopds.conf')):
        self.config = configparser.ConfigParser()
        self.filename = filename
        self.config.read(self.filename, 'utf-8')

        self.NAME = self.config.get(self.CFG_G, 'name', fallback='Simple OPDS Catalog')
        self.ROOT_URL = self.config.get(self.CFG_G, 'root_url', fallback='http://home/')
        self.PORT = self.config.get(self.CFG_G, 'port', fallback=8000)

        self.ENGINE = self.config.get(self.CFG_G, 'engine', fallback='sqlite:///')
        self.DB_NAME = self.config.get(self.CFG_G, 'db_name', fallback=os.path.join(PY_PATH, 'db', 'sopds.db'))
        self.DB_USER = self.config.get(self.CFG_G, 'db_user', fallback='sopds')
        self.DB_PASS = self.config.get(self.CFG_G, 'db_pass', fallback='sopds_pass')
        self.DB_HOST = self.config.get(self.CFG_G, 'db_host', fallback='localhost')
        self.DB_CHARSET = self.config.get(self.CFG_G, 'db_charset', fallback='utf-8')

        self.ROOT_LIB = os.path.abspath(self.config.get(self.CFG_G, 'root_lib', fallback=r'\documents\books'))
        self.COVER_PATH = os.path.abspath(self.config.get(self.CFG_G, 'cover_path', fallback=r'\documents\covers'))
        self.FORMATS = self.config.get(self.CFG_G, 'formats', fallback='.pdf .djvu .fb2 .txt')
        self.DUBLICATES_FIND = self.config.getboolean(self.CFG_G, 'dublicates_find', fallback=True)
        self.DUBLICATES_SHOW = self.config.getboolean(self.CFG_G, 'dublicates_show', fallback=False)
        self.FB2PARSE = self.config.getboolean(self.CFG_G, 'fb2parse', fallback=True)
        self.ZIPSCAN = self.config.getboolean(self.CFG_G, 'zipscan', fallback=True)
        self.ZIPRESCAN = self.config.getboolean(self.CFG_G, 'ziprescan', fallback=False)
        self.COVER_EXTRACT = self.config.getboolean(self.CFG_G, 'cover_extract', fallback=True)
        self.LAST_SCAN = self.config.getfloat(self.CFG_G, 'last_scan', fallback=time.time())

        self.FB2HSIZE = self.config.getint(self.CFG_G, 'fb2hsize', fallback=0)
        self.MAXITEMS = self.config.getint(self.CFG_G, 'maxitems', fallback=50)
        self.SPLITAUTHORS = self.config.getint(self.CFG_G, 'splitauthors', fallback=300)
        self.SPLITTITLES = self.config.getint(self.CFG_G, 'splittitles', fallback=300)
        self.COVER_SHOW = self.config.getint(self.CFG_G, 'cover_show', fallback=0)
        self.COVER_THUMBNAIL_SIZE = self.config.getint(self.CFG_G, 'cover_thumbnail_size', fallback=144)
        zip_codepage = self.config.get(self.CFG_G, 'zip_codepage', fallback='cp866')

        if self.COVER_EXTRACT:
            self.FB2SIZE = 0

        self.EXT_LIST = self.FORMATS.lower().split()

        if zip_codepage.lower() in {'cp437', 'cp866', 'cp1251', 'utf-8'}:
            self.ZIP_CODEPAGE = zip_codepage.lower()
        else:
            self.ZIP_CODEPAGE = 'cp437'

        CFG_S = 'site'
        self.SITE_ID = self.config.get(CFG_S, 'id', fallback='http://home/')
        self.SITE_TITLE = self.config.get(CFG_S, 'title', fallback='OPDS Catalog')
        self.SITE_ICON = self.config.get(CFG_S, 'icon', fallback='http://home/favicon.ico')
        self.SITE_AUTOR = self.config.get(CFG_S, 'autor', fallback='Victor')
        self.SITE_URL = self.config.get(CFG_S, 'url', fallback='http://home')
        self.SITE_EMAIL = self.config.get(CFG_S, 'email', fallback='victor@home')
        self.SITE_MAINTITLE = self.config.get(CFG_S, 'main_title', fallback='Root of Simple OPDS Catalog')

    def set_last_update(self):
        self.LAST_SCAN = time.time()
        self.config.set(self.CFG_G, 'last_scan', str(self.LAST_SCAN))
        with open(self.filename, 'w') as configfile:
            self.config.write(configfile)
        
        
cfg = CfgReader()


class Author:
    def __init__(self, author):
        ns = author.tag.split('}')[0][1:]
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
        self.content_type = ''
        if _id[0] == '#':
            binary = root.find("*/[@id='{:s}']".format(_id[1:]))
            if binary != None:
                self.content_type = binary.get('content-type').lower()
                self.image = base64.b64decode(binary.text)


class FictionBook:

    def __init__(self, filename):
        if isinstance(filename, str):
            if os.path.exists(filename):
                try:
                    self.tree = ET.parse(filename)
                    self.root = self.tree.getroot()
                    self.parsed = True
                except ET.ParseError:
                    self.parsed = False
            else:
                self.parsed = False
        elif hasattr(filename, 'read'):
            try:
                self.root = ET.fromstring(filename.read())
                self.parsed = True
            except ET.ParseError:
                self.parsed = False
        else:
            self.parsed = False
        if self.parsed:
            ns = self.root.tag.split('}')[0][1:]
            desc = self.root.find(ET.QName(ns, 'description').text)
            ti = desc.find(ET.QName(ns, 'title-info').text)
            self.genres = []
            for genre in ti.iter(ET.QName(ns, 'genre').text):
                self.genres.append(genre.text.lower().strip(' \'\"\&()-.#[]\\\`'))
            self.authors = [Author(author) for author in ti.iter(ET.QName(ns, 'author').text)]
            self.lang = ti.findtext(ET.QName(ns, 'lang').text, 'ru').strip(' \'\"')
            self.title = ti.findtext(ET.QName(ns, 'book-title').text, '').strip(' \'\"\&()-.#[]\\\`')
            annotation = ti.find(ET.QName(ns, 'annotation').text)
            if annotation:
                self.annotation = ET.tostring(annotation, 'unicode', 'text')
            else:
                self.annotation = ''
            coverpage = ti.find(ET.QName(ns, 'coverpage').text)
            self.cover = None
            if coverpage is not None:
                image = coverpage.find(ET.QName(ns, 'image').text)
                if image is not None:
                    self.cover = Image(self.root, image)
            sequence = ti.find(ET.QName(ns, 'sequence').text)
            if sequence is not None:
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
    #ret['cover_name'] = ''
    #ret['cover_image'] = ''

    return book


def processzip(db, path, zip_filename, cfg):
    rel_path = os.path.relpath(path, cfg.ROOT_LIB)
    rel_file = os.path.join(rel_path, zip_filename)
    path_file = os.path.join(path, zip_filename)
    if cfg.ZIPRESCAN or dbase.zipisscanned(rel_file) == 0:
        z = zipfile.ZipFile(path_file, 'r', allowZip64=True)
        file_list = z.namelist()
        if VERBOSE:
            print('Start process ZIPped file: {:s}'.format(zip_filename))
        for filename in file_list:
            try:
                processfile(db, path_file, filename, cfg, archive=z)
            except:
                print('Error processing zip archive:', zip_filename, ' file: ', filename)
        z.close()
    else:
        if VERBOSE:
            print('Skip ZIP archive: ', rel_file, '. Already scanned.')


def processfile(db, path, filename, cfg, archive=None):
    rel_path = os.path.relpath(path, cfg.ROOT_LIB)
    if not db.findbook(filename, rel_path):
        cat_id = db.addcattree(rel_path, 1 if archive else 0)
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.fb2' and cfg.FB2PARSE:
            if archive:
                fb = FictionBook(archive.open(filename))
                file_size = archive.getinfo(filename).file_size
            else:
                full_path = os.path.join(path, filename)
                file_size = os.path.getsize(full_path)
                fb = FictionBook(full_path)
            book = db.addbook(filename, rel_path, cat_id, ext, fb.title, fb.lang, file_size, 1 if archive else 0,
                                    cfg.DUBLICATES_FIND, fb.annotation)
            if VERBOSE:
                print('Add file: {:s} {:s}'.format(path, filename))
            for author in fb.authors:
                author = dbase.addauthor(author.first_name, author.last_name)
                db.addbauthor(book.book_id, author.author_id)
            for genre in fb.genres:
                db.addbgenre(book.book_id, dbase.addgenre(genre).genre_id)
            if cfg.COVER_EXTRACT and fb.cover:
                ext = mimetypes.guess_extension(fb.cover.content_type)
                if ext:
                    fn = str(book.book_id) + ext
                    fp = os.path.join(cfg.COVER_PATH, fn)
                    fp_thubnail = os.path.join(cfg.COVER_PATH, 'thumbnails', fn)
                    img = open(fp, 'wb')
                    img.write(fb.cover.image)
                    img.close()
                    image = PIL.Image.open(fp)
                    image.thumbnail((cfg.COVER_THUMBNAIL_SIZE, cfg.COVER_THUMBNAIL_SIZE))
                    image.save(fp_thubnail)
                    db.addcover(book.book_id, fn, fb.cover.content_type)
                    if VERBOSE:
                        print('Add cover: {}'.format(fp))
    else:
        if VERBOSE:
            print('Skip file: ', filename, '. Already scanned.')


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Simple OPDS Scaner - program for scan your e-book directory and store data to database.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-i', '--init', help='Init library database', action='store_true')
    group.add_argument('-s', '--scan-all', help='Full rescan all library', action='store_true')
    group.add_argument('-l', '--last', help='Scan files from date after last scan', action='store_true')
    parser.add_argument('-v', '--verbose', help='Enable verbose output', action='store_true')
    parser.add_argument('-c', '--config', help='Config file path')

    args = parser.parse_args()
    VERBOSE = args.verbose

    if VERBOSE:
        print('Option set: init = %s, scan-all = %s, scan-last = %s, config path = %s' % (args.init, args.scan_all, args.last, args.config))

    if args.config and os.path.isfile(args.config):
        cfg = CfgReader(args.config)
    else:
        cfg = CfgReader()

    dbase = opdsdb.opdsDatabase(cfg.ENGINE+cfg.DB_NAME, cfg.DB_USER, cfg.DB_PASS, cfg.DB_HOST, cfg.ROOT_LIB)
    dbase.open_db()

    if VERBOSE:
        print(dbase.print_db_err())

    if cfg.COVER_EXTRACT:
        if not os.path.isdir(cfg.COVER_PATH):
            os.mkdir(cfg.COVER_PATH)
        if not os.path.isdir(os.path.join(cfg.COVER_PATH, 'thumbnails')):
            os.mkdir(os.path.join(cfg.COVER_PATH, 'thumbnails'))

    ext_set = {x for x in cfg.EXT_LIST}
    if VERBOSE:
        print(ext_set)

    if args.init:
        dbase.init_db()
    elif args.scan_all:
        for full_path, dirs, files in os.walk(cfg.ROOT_LIB):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext == '.zip' and cfg.ZIPSCAN:
                    if VERBOSE:
                        print('Add file: {:s} {:s}'.format(full_path, filename))
                    processzip(dbase, full_path, filename, cfg)
                elif ext in ext_set:
                    processfile(dbase, full_path, filename, cfg)
        cfg.set_last_update()
    elif args.last:
        for full_path, dirs, files in os.walk(cfg.ROOT_LIB):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                mod_time = os.path.getmtime(os.path.join(full_path, filename))
                if cfg.LAST_SCAN < mod_time:
                    if ext == '.zip' and cfg.ZIPSCAN:
                        processzip(dbase, full_path, filename, cfg)
                    elif ext in ext_set:
                        if VERBOSE:
                            print('Add file: {:s} {:s}'.format(full_path, filename))
                        processfile(dbase, full_path, filename, cfg)
        cfg.set_last_update()

    dbase.close_db()
