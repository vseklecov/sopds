__author__ = 'vseklecov'

import os
import xml.etree.ElementTree as ET

import db


def fb2parse(filename):
    ret = {'genres': [], 'authors': []}
    if isinstance(filename, str):
        tree = ET.parse(filename)
    else:
        tree = ET.fromstring(filename.read())
    root = tree.getroot()
    ns = root.tag.split('}')[0][1:]

    description = root.find(ET.QName(ns, 'description').text)
    title_info = description.find(ET.QName(ns, 'title-info').text)
    ret['genres'] = [genre.text for genre in title_info.iter(ET.QName(ns, 'genre').text)]

    for author in title_info.iter(ET.QName(ns, 'author').text):
        ad = {'last_name': author.findtext(ET.QName(ns, 'last-name').text, ''),
              'first_name': author.findtext(ET.QName(ns, 'first-name').text, '')}
        ret['authors'].append(ad)

    ret['lang'] = title_info.findtext(ET.QName(ns, 'lang').text, '')
    ret['book_title'] = title_info.findtext(ET.QName(ns, 'book-title').text, '')
    ret['cover_name'] = ''
    ret['cover_image'] = ''

    return ret


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

    import utils

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
        cfg = utils.CfgReader(args.config)
    else:
        cfg = utils.CfgReader()

    dbase = db.opdsDatabase(cfg.ENGINE+cfg.DB_NAME, cfg.DB_USER, cfg.DB_PASS, cfg.DB_HOST, cfg.ROOT_LIB)
    dbase.open_db()

    if args.verbose:
        print(dbase.print_db_err())

    if cfg.COVER_EXTRACT:
        if not os.path.isdir(os.path.join(utils.PY_PATH,'covers')):
            os.mkdir(os.path.join(utils.PY_PATH,'covers'))

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

    # if len(sys.argv) == 1:
    #     for fn in os.listdir('.'):
    #         if os.path.splitext(fn)[1].lower() == '.fb2':
    #             print(fb2parse(fn))
    # else:
    #     for fn in os.listdir(sys.argv[1]):
    #         if os.path.splitext(fn)[1].lower() == '.fb2':
    #             print(fb2parse(os.path.join(sys.argv[1], fn)))
