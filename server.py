# -*- coding: utf-8 -*-
from fb2parser import fb2parse

__author__ = 'vseklecov'

import io
import logging
import mimetypes
import os
from urllib.parse import parse_qs
from wsgiref.validate import validator
from wsgiref.simple_server import make_server
import zipfile

import db as sopdsdb
from utils import CfgReader, FictionBook

cfg = CfgReader()

MAIN_MENU = 0
LIST_CAT = 1
LIST_AUTHORS_CNT = 2
LIST_TITLE_CNT = 3
LIST_GENRE_CNT = 11
LIST_GENRE_SUB_CNT = 12
LIST_AUTHOR_CNT = 5

LIST_TITLE_SEARCH = 10
LIST_LAST = 4
LIST_BOOK = 6
LIST_SUBSECTION = 13

BOOK = 7

OUT_BOOK = 8
OUT_ZIP_BOOK = 9
OUT_COVER = 99


class Link:
    def __init__(self, href, _type='application/atom+xml', **kwargs):
        self.type = _type
        self.href = href
        self.args = dict(kwargs)
        for k in self.args:
            self.args[k] = pyatom.escape(self.args[k], True)

    def to_dict(self):
        return dict(self.args, type=self.type, href=self.href)

    def __str__(self):
        return '<link type="{0:s}" href="{1:s}" {2:s}/>'. \
            format(self.type, self.href, ' '.join('{0:s}="{1:s}"'.format(k, self.args[k]) for k in self.args))


class NavigationLink(Link):
    def __init__(self, href, **kwargs):
        Link.__init__(self, href, _type='application/atom+xml;profile=opds-catalog;kind=navigation', **kwargs)


class AsqusitionLink(Link):
    def __init__(self, href, **kwargs):
        Link.__init__(self, href, _type='application/atom+xml;profile=opds-catalog;kind=asqusition', **kwargs)


#######################################################################
#
# Вспомогательные функции
#
def translit(s):
    """Russian translit: converts 'привет'->'privet'"""
    assert s is not str, "Error: argument MUST be string"

    table1 = str.maketrans("абвгдеёзийклмнопрстуфхъыьэАБВГДЕЁЗИЙКЛМНОПРСТУФХЪЫЬЭ",
                           "abvgdeezijklmnoprstufh'y'eABVGDEEZIJKLMNOPRSTUFH'Y'E")
    table2 = {'ж': 'zh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ю': 'ju', 'я': 'ja', 'Ж': 'Zh', 'Ц': 'Ts',
              'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch', 'Ю': 'Ju', 'Я': 'Ja'}
    for k in table2.keys():
        s = s.replace(k, table2[k])
    return s.translate(table1)


def make_feed():
    _author = dict(name=cfg.SITE_AUTOR, uri=cfg.SITE_URL, email=cfg.SITE_EMAIL)
    _feed = pyatom.OPDSAtomFeed(id=cfg.SITE_ID, title=cfg.SITE_TITLE, icon=cfg.SITE_ICON, author=_author)
    _feed.links.append(NavigationLink('/', rel='start', title=cfg.SITE_MAINTITLE).to_dict())
    return _feed


def make_entry_book(book):
    _authors = [dict(name=str(author)) for author in book.authors]
    _entry = pyatom.FeedEntry(title=pyatom.escape(book.title),
                              updated=book.registerdate,
                              id='list:book:{0:d}'.format(book.book_id),
                              content_type='text',
                              content=', '.join([str(author) for author in book.authors]),
                              author=_authors)
    _id = '/?id=07{0:d}'.format(book.book_id)
    _entry.links.append(Link(_id, rel='alternate').to_dict())
    _entry.links.append(AsqusitionLink(_id, rel='subsection').to_dict())
    _entry.links.extend(covers(book.cover, book.cover_type, book.book_id))
    return _entry


def make_href(id_value, slice_value=None, page_value=None):
    ret = '/?id={:02d}'.format(id_value)
    if slice_value:
        if isinstance(slice_value, str):
            ret += '{:s}'.format(slice_value)
        else:
            ret += '{:d}'.format(slice_value)
    if page_value:
        ret += '&amp;page={:d}'.format(page_value)
    return ret


def make_book(book):
    href_1 = make_href(OUT_BOOK, book.book_id)
    href_2 = make_href(OUT_ZIP_BOOK, book.book_id)
    _content = 'Название книги: {:s}\nАвтор(ы): {:s}\nЖанры: {:s}\nРазмер файла : {:d} Кб'. \
        format(book.title, ', '.join([str(author) for author in book.authors]),
               ', '.join([genre.subsection for genre in book.genres]), book.filesize // 1000)
    _entry = pyatom.FeedEntry(title=pyatom.escape(book.title, True) or book.filename,
                              id='main:book:{:d}'.format(book.book_id),
                              updated=book.registerdate,
                              author=[dict(name=str(author)) for author in book.authors],
                              content_type='text',
                              content=_content)
    _entry.links.append(Link(href_1, _type='application/' + book.format, rel='alternate').to_dict())
    _entry.links.append(Link(href_1, _type='application/' + book.format,
                             rel='http://opds-spec.org/acquisition').to_dict())
    _entry.links.append(Link(href_2, _type='application/' + book.format + '+zip',
                             rel='http://opds-spec.org/acquisition').to_dict())
    _entry.links.extend(covers(book.cover, book.cover_type, book.book_id))
    return _entry


def add_previous_link(feed, id_value, page_value):
    feed.links.append(AsqusitionLink(make_href(id_value, page_value=page_value - 1),
                                     rel='prev', title='Previous page').to_dict())


def add_next_link(feed, id_value, page_value):
    feed.links.append(AsqusitionLink(make_href(id_value, page_value=page_value + 1),
                                     rel='next', title='Next page').to_dict())


def letter_from_slice(slice_value):
    i = slice_value
    letter = ""
    while i > 0:
        letter = chr(i % 10000) + letter
        i //= 10000
    return letter


def slice_from_letter(letters):
    _slice = ''
    for ch in letters:
        _slice += '{:04d}'.format(ord(ch))
    return _slice


###########################################################################################################
# Основное меню
#
def main_menu():
    _books, _authors, _catalogs = opdsdb.getdbinfo(cfg.DUBLICATES_SHOW)

    _feed = make_feed()
    _feed.links.append(Link('opensearch.xml', type='application/opensearchdescription+xml', rel='search').to_dict())
    _feed.links.append(Link('/?search={searchTerms}', rel='search').to_dict())

    _feed.add(pyatom.FeedEntry(title='По каталогам', id='main:catalogs', content_type='text',
                               content='Каталогов: {:d}, книг: {:d}.'.format(_catalogs, _books),
                               links=[NavigationLink(make_href(LIST_CAT)).to_dict()]))

    _feed.add(pyatom.FeedEntry(title='По авторам', id='main:authors', content_type='text',
                               content='Авторов: {0:d}, книг: {1:d}.'.format(_authors, _books),
                               links=[NavigationLink(make_href(LIST_AUTHORS_CNT)).to_dict()]))

    _feed.add(pyatom.FeedEntry(title='По наименованию', id='main:titles', content_type='text',
                               content='Авторов: {0:d}, книг: {1:d}.'.format(_authors, _books),
                               links=[NavigationLink(make_href(LIST_TITLE_CNT)).to_dict()]))

    _feed.add(pyatom.FeedEntry(title='По жанрам', id='main:genres', content_type='text',
                               content='Авторов: {0:d}, книг: {1:d}.'.format(_authors, _books),
                               links=[NavigationLink(make_href(LIST_GENRE_CNT)).to_dict()]))

    _feed.add(pyatom.FeedEntry(title='Последние добавленные', id='main:last', content_type='text',
                               content='Книг: {0:d}.'.format(min(cfg.MAXITEMS, _books)),
                               links=[NavigationLink(make_href(LIST_LAST)).to_dict()]))
    return _feed


def covers(cover, cover_type, book_id):
    have_extracted_cover = 0
    links = []
    if cfg.COVER_SHOW != 0:
        if cfg.COVER_SHOW != 2:
            if cover and cover != '':
                _id = '../covers/{0:s}'.format(cover)
                _id_t = '../covers/thumbnails/{0:s}'.format(cover)
                links.append(Link(_id, rel='http://opds-spec.org/image', _type=cover_type).to_dict())
                links.append(Link(_id, rel='x-stanza-cover-image', _type=cover_type).to_dict())
                links.append(Link(_id_t, rel='http://opds-spec.org/image/thumbnail', _type=cover_type).to_dict())
                links.append(Link(_id_t, rel='x-stanza-cover-image-thumbnail', _type=cover_type).to_dict())
                have_extracted_cover = 1
        if cfg.COVER_SHOW == 2 or (cfg.COVER_SHOW == 3 and have_extracted_cover == 0):
            _id = make_href(OUT_COVER, book_id)
            links.append(dict(href=_id, rel='http://opds-spec.org/image'))
            #links.append(dict(href=_id, rel='x-stanza-cover-image'))
            links.append(dict(href=_id, rel='http://opds-spec.org/image/thumbnail'))
            #links.append(dict(href=_id, rel='x-stanza-cover-image-thumbnail'))
    return links


#########################################################
# Выбрана сортировка "По каталогам"
#
def list_of_catalogs(slice_value=0, page_value=0):
    _feed = make_feed()
    if page_value > 0:
        add_previous_link(_feed, LIST_CAT, page_value)
    for (item_type, item_id, item_name, item_path, reg_date, item_title) in opdsdb.getitemsincat(slice_value,
                                                                                                 cfg.MAXITEMS,
                                                                                                 page_value):
        if item_type == 1:
            _id = make_href(LIST_CAT, item_id)
            _entry = pyatom.FeedEntry(title=item_title or item_name,
                                      id='catalog:{:d}'.format(item_id),
                                      updated=reg_date)
            _entry.links.append(AsqusitionLink(_id, rel='subsection').to_dict())
            _entry.links.append(Link(_id, rel='alternate').to_dict())
            _feed.add(_entry)
        elif item_type == 2:
            book = opdsdb.getbook(item_id)
            _feed.add(make_book(book))

    if opdsdb.next_page:
        add_next_link(_feed, LIST_CAT, page_value)
    return _feed


#########################################################
# Выбрана сортировка "По авторам" - выбор по несскольким первым буквам автора
#
def list_of_authors(slice_value):
    _feed = make_feed()
    letter = letter_from_slice(slice_value)
    logging.debug('letter: "{:s}"'.format(letter))
    for (letters, cnt) in opdsdb.getauthor_2letters(letter):
        if cfg.SPLITTITLES == 0 or cnt <= cfg.SPLITTITLES or len(letters) > 10:
            _id = make_href(LIST_AUTHOR_CNT, slice_from_letter(letters))
        else:
            _id = make_href(LIST_AUTHORS_CNT, slice_from_letter(letters))
        _entry = pyatom.FeedEntry(title='-= ' + pyatom.escape(letters) + ' =-',
                                  id='authors:' + pyatom.escape(letters),
                                  content_type='text',
                                  content='Всего: {:d} автора(ов).'.format(cnt))
        _entry.links.append(Link(_id, rel='alternate').to_dict())
        _entry.links.append(AsqusitionLink(_id, rel='subsection').to_dict())
        _feed.add(_entry)
    return _feed


#########################################################
# Выбрана сортировка "По наименованию" - выбор по нескольким первым буквам наименования
#
def list_of_title(slice_value):
    _feed = make_feed()
    letter = letter_from_slice(slice_value)
    for (letters, cnt) in opdsdb.gettitle_2letters(letter, cfg.DUBLICATES_SHOW):
        if cfg.SPLITTITLES == 0 or cnt <= cfg.SPLITTITLES or len(letters) > 10:
            _id = make_href(LIST_TITLE_SEARCH, slice_from_letter(letters))
        else:
            _id = make_href(LIST_TITLE_CNT, slice_from_letter(letters))
        _entry = pyatom.FeedEntry(title='-= ' + pyatom.escape(letters) + ' =-',
                                  id='title:' + pyatom.escape(letters),
                                  content_type='text',
                                  content=' Всего: {:d} наименований.'.format(cnt))
        _entry.links.append(Link(_id, rel='alternate').to_dict())
        _entry.links.append(AsqusitionLink(_id, rel='subsection').to_dict())
        _feed.add(_entry)

    return _feed


#########################################################
# Выдача списка книг по наименованию или на основании поискового запроса
#
def list_of_title_or_search(slice_value, page_value, search_term):
    _feed = make_feed()
    if page_value > 0:
        add_previous_link(_feed, LIST_TITLE_SEARCH, page_value)
    letter = letter_from_slice(slice_value) if slice_value >= 0 else "%" + search_term
    for book in opdsdb.getbooksfortitle(letter, cfg.MAXITEMS, page_value, cfg.DUBLICATES_SHOW):
        _feed.add(make_book(book))
    if opdsdb.next_page:
        add_next_link(_feed, LIST_TITLE_SEARCH, page_value)
    return _feed


#########################################################
# Выбрана сортировка "По жанрам" - показ секций
#
def list_of_genre():
    _feed = make_feed()
    for (genre_id, genre_section, cnt) in opdsdb.getgenres_sections():
        _id = make_href(LIST_GENRE_SUB_CNT, genre_id)
        _entry = pyatom.FeedEntry(title=genre_section,
                                  id='genre:{:d}'.format(genre_id),
                                  content_type='text',
                                  content=' Всего: {:d} книг.'.format(cnt))
        _entry.links.append(Link(_id, rel='alternate').to_dict())
        _entry.links.append(AsqusitionLink(_id, rel='subsection').to_dict())
        _feed.add(_entry)
    return _feed


#########################################################
# Выбрана сортировка "По жанрам" - показ подсекций
#
def list_of_genre_subsections(slice_value):
    _feed = make_feed()
    for (genre_id, genre_subsection, cnt) in opdsdb.getgenres_subsections(slice_value):
        _id = make_href(LIST_SUBSECTION, genre_id)
        _entry = pyatom.FeedEntry(title=genre_subsection,
                                  id='genre:{:d}'.format(genre_id),
                                  content_type='text',
                                  content=' Всего: {:d} книг.'.format(cnt))
        _entry.links.append(Link(_id, rel='alternate').to_dict())
        _entry.links.append(AsqusitionLink(_id, rel='subsection').to_dict())
        _feed.add(_entry)
    return _feed


#########################################################
# Выдача списка книг по жанру
#
def list_of_subsection(slice_value, page_value):
    _feed = make_feed()
    if page_value > 0:
        add_previous_link(_feed, LIST_SUBSECTION, page_value)
    for book in opdsdb.getbooksforgenre(slice_value, cfg.MAXITEMS, page_value, cfg.DUBLICATES_SHOW):
        _feed.add(make_book(book))
    if opdsdb.next_page:
        add_next_link(_feed, LIST_SUBSECTION, page_value)
    return _feed


#########################################################
# Выбрана сортировка "Последние поступления"
#
def list_of_last():
    _feed = make_feed()
    for book in opdsdb.getlastbooks(cfg.MAXITEMS):
        _feed.add(make_book(book))
    return _feed


#########################################################
# Выдача списка авторов
#
def list_authors(slice_value, page_value):
    _feed = make_feed()
    if page_value > 0:
        add_previous_link(_feed, LIST_AUTHOR_CNT, page_value)
    letter = letter_from_slice(slice_value)
    for (author_id, first_name, last_name, cnt) in opdsdb.getauthorsbyl(letter, cfg.MAXITEMS, page_value,
                                                                        cfg.DUBLICATES_SHOW):
        _id = make_href(LIST_BOOK, author_id)
        _entry = pyatom.FeedEntry(title='{:s} {:s}'.format(last_name, first_name),
                                  id='author:{:d}'.format(author_id),
                                  content_type='text',
                                  content=' Всего: {:d} книг.'.format(cnt))
        _entry.links.append(Link(_id, rel='alternate').to_dict())
        _entry.links.append(AsqusitionLink(_id, rel='subsection').to_dict())
        _feed.add(_entry)
    if opdsdb.next_page:
        add_next_link(_feed, LIST_AUTHOR_CNT, page_value)
    return _feed


#########################################################
# Выдача списка книг по автору
#
def list_book_of_author(slice_value, page_value):
    _feed = make_feed()
    if page_value > 0:
        add_previous_link(_feed, LIST_BOOK, page_value)
    for book in opdsdb.getbooksforauthor(slice_value, cfg.MAXITEMS, page_value, cfg.DUBLICATES_SHOW):
        _feed.add(make_book(book))
    if opdsdb.next_page:
        add_next_link(_feed, LIST_BOOK, page_value)
    return _feed


#########################################################
# Выдача ссылок на книгу
#
def list_of_ref(book_id):
    _feed = make_feed()
    _feed.links.append(AsqusitionLink(make_href(BOOK, book_id), rel='self').to_dict())
    book = opdsdb.getbook(book_id)
    if book:
        _feed.add(make_book(book))

    # genres = ""
    # for (section, genre) in opdsdb.getgenres(slice_value):
    #        ret += enc_print('<category term="%s" label="%s" />' % (genre, genre))
    #         if len(genres) > 0:
    #             genres += ', '
    #         genres += genre

    return _feed


#########################################################
# Выдача файла книги
#
def out_file_of_book(book_id):
    book = opdsdb.getbook(book_id)
    full_path = os.path.join(cfg.ROOT_LIB, book.path)
    # HTTP Header
    status = '200 OK'
    headers = [('Content-Type', 'application/octet-stream; name="' + book.filename + '"'),
               ('Content-Disposition', 'attachment; filename=' + translit(book.filename)),
               ('Content-Transfer-Encoding', 'binary')]
    buf = ''
    if book.cat_normal():
        file_path = os.path.join(full_path, book.filename)
        if os.path.exists(file_path):
            book_size = os.path.getsize(file_path.encode('utf-8'))
            headers.append(('Content-Length', str(book_size)))
            fo = open(file_path, "rb")
            buf = fo.read()
            fo.close()
        else:
            status = '404 Not Found'
    elif book.cat_zip():
        if os.path.exists(full_path):
            z = zipfile.ZipFile(full_path, 'r', allowZip64=True)
            book_size = z.getinfo(book.filename).file_size
            headers.append(('Content-Length', str(book_size)))
            fo = z.open(book.filename)
            buf = fo.read()
            fo.close()
            z.close()
        else:
            status = '404 Not Found'
    return status, headers, buf


#########################################################
# Выдача файла книги в ZIP формате
#
def out_zipfile_of_book(book_id):
    book = opdsdb.getbook(book_id)
    full_path = os.path.join(cfg.ROOT_LIB, book.path)
    trans_name = translit(book.filename)
    # HTTP Header
    status = '200 OK'
    headers = [('Content-Type', 'application/zip; name="{0:s}"'.format(book.filename)),
               ('Content-Disposition', 'attachment; filename={0:s}.zip'.format(trans_name)),
               ('Content-Transfer-Encoding', 'binary')]
    buf = ''
    dio = io.BytesIO()
    zo = zipfile.ZipFile(dio, 'w', zipfile.ZIP_DEFLATED)
    if book.cat_type == sopdsdb.CAT_NORMAL:
        file_path = os.path.join(full_path, book.filename)
        if os.path.exists(file_path):
            zo.write(file_path.encode('utf-8'), trans_name)
            zo.close()
            buf = dio.getvalue()
            headers.append(('Content-Length', str(len(buf))))
        else:
            status = '404 Not Found'
    elif book.cat_type == sopdsdb.CAT_ZIP:
        if os.path.exists(full_path):
            z = zipfile.ZipFile(full_path, 'r', allowZip64=True)
            fo = z.open(book.filename)
            buf = fo.read()
            fo.close()
            z.close()
            zo.writestr(trans_name, buf)
            zo.close()
            buf = dio.getvalue()
            headers.append(('Content-Length', str(len(buf))))
        else:
            status = '404 Not Found'
    return status, headers, buf


#########################################################
# Выдача Обложки На лету
#
def get_cover(book_id):
    book = opdsdb.getbook(book_id)
    no_cover = True
    status = '200 OK'
    headers = []
    buf = b''
    if book.format == 'fb2':
        full_path = os.path.join(cfg.ROOT_LIB, book.path)
        if book.cat_normal():
            file_path = os.path.join(full_path, book.filename)
            fb2 = FictionBook(file_path)
        else:
            z = zipfile.ZipFile(full_path)
            f = z.open(book.filename)
            fb2 = FictionBook(f)
        if fb2.cover is not None:
            try:
                buf = fb2.cover.image
                ictype = fb2.cover.content_type
                headers = [('Content-Type', ictype), ('Content-Length', str(len(buf)))]
                no_cover = False
            except:
                no_cover = True

    if no_cover:
        if os.path.exists(cfg.NOCOVER_IMG):
            headers = [('Content-Type', 'image/jpeg')]
            f = open(cfg.NOCOVER_IMG, "rb")
            buf = f.read()
            f.close()
            headers.append(('Content-Length', str(len(buf))))
        else:
            status = '404 Not Found'

    return status, headers, buf


def out_file(path):
    status = '200 OK'
    headers = []
    buf = b''
    ictype = mimetypes.guess_type(path)[0]
    if ictype == None:
        status = '404 Not Found'
        return status, headers, buf

    headers = [('Content-Type', ictype)]
    p, filename = os.path.split(path)
    if p.strip(os.sep+os.altsep) == 'covers':
        full_path = os.path.join(cfg.COVER_PATH, filename)
    elif p.strip(os.sep+os.altsep) == 'covers/thumbnails':
        full_path = os.path.join(cfg.COVER_PATH, 'thumbnails', filename)
    else:
        full_path = filename
    logging.debug('path: %s, full_path: "%s"' % (p, full_path))
    if os.path.exists(full_path):
        f = open(full_path, 'rb')
        buf = f.read()
        f.close()
        headers.append(('Content-Length', str(len(buf))))
    else:
        status = '404 Not Found'
    return status, headers, buf

import pyatom


def simple_app(environ, start_response):

    path_info = environ['PATH_INFO']
    logging.debug('path_info: "%s"' % path_info)
    if path_info != '/':
        logging.debug(path_info)
        status, headers, buf = out_file(path_info)
        start_response(status, headers)
        return [buf]

    d = parse_qs(environ['QUERY_STRING'])
    logging.debug(d)

    type_value = 0
    slice_value = 0
    page_value = 0
    search_term = ''

    if 'id' in d:
        id_value = d.get('id', ['0'])[0]
        if id_value.isdigit():
            if len(id_value) > 1:
                type_value = int(id_value[:2])
            if len(id_value) > 2:
                slice_value = int(id_value[2:])
    if 'page' in d:
        page = d.get('page', ['0'])[0]
        if page.isdigit():
            page_value = int(page)
    if 'search' in d:
        search_term = d.get('search', [''])[0]
        type_value = 10
        slice_value = -1
        id_value = "10&amp;search=" + search_term

    status = '200 OK'
    headers = [('Content-type', 'text/xml; charset=utf-8')]
    logging.debug('type_value: "{:d}"'.format(type_value))
    if type_value == 0:
        feed = main_menu()
    elif type_value == LIST_CAT:
        feed = list_of_catalogs(slice_value, page_value)
    elif type_value == LIST_AUTHORS_CNT:
        feed = list_of_authors(slice_value)
    elif type_value == LIST_TITLE_CNT:
        feed = list_of_title(slice_value)
    elif type_value == LIST_TITLE_SEARCH:
        feed = list_of_title_or_search(slice_value, page_value, search_term)
    elif type_value == LIST_GENRE_CNT:
        feed = list_of_genre()
    elif type_value == LIST_GENRE_SUB_CNT:
        feed = list_of_genre_subsections(slice_value)
    elif type_value == LIST_SUBSECTION:
        feed = list_of_subsection(slice_value, page_value)
    elif type_value == LIST_LAST:
        feed = list_of_last()
    elif type_value == LIST_AUTHOR_CNT:
        feed = list_authors(slice_value, page_value)
    elif type_value == LIST_BOOK:
        feed = list_book_of_author(slice_value, page_value)
    elif type_value == BOOK:
        feed = list_of_ref(slice_value)
    elif type_value == OUT_BOOK:
        status, headers, ret = out_file_of_book(slice_value)
        start_response(status, headers)
        return [ret]
    elif type_value == OUT_ZIP_BOOK:
        status, headers, ret = out_zipfile_of_book(slice_value)
        start_response(status, headers)
        return [ret]
    elif type_value == OUT_COVER:
        status, headers, ret = get_cover(slice_value)
        start_response(status, headers)
        return [ret]
    else:
        feed = make_feed()

    start_response(status, headers)
    logging.debug(feed)
    return [feed.to_bytestring()]


if __name__ == '__main__':
    logging.basicConfig(filename='server.log', level=logging.DEBUG)

    opdsdb = sopdsdb.opdsDatabase(cfg.ENGINE + cfg.DB_NAME, cfg.DB_USER, cfg.DB_PASS, cfg.DB_HOST, cfg.ROOT_LIB)
    opdsdb.open_db()

    validator_app = validator(simple_app)
    httpd = make_server('', cfg.PORT, validator_app)
    print('Serving on port {0:d}...'.format(cfg.PORT))
    httpd.serve_forever()

    opdsdb.close_db()
