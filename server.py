# -*- coding: utf-8 -*-
__author__ = 'vseklecov'

import codecs

import logging
import os
from urllib.parse import parse_qs
import time
from wsgiref.validate import validator
from wsgiref.simple_server import make_server
import zipfile

import db as sopdsdb
from utils import CfgReader

cfg = CfgReader()


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


def websym(s):
    """Replace special web-symbols"""
    result = s
    table = {'&': '&amp;', '<': '&lt;'}
    for k in table.keys():
        result = result.replace(k, table[k])
    return result


def enc_print(string=''):
    #    return string.encode(encoding) + b'\n'
    return string + '\n'


def header():
    #    ret += enc_print('Content-Type: text/xml; charset='+charset)
    #    ret += enc_print()
    ret = enc_print('<?xml version="1.0" encoding="utf-8"?>')
    ret += enc_print('<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opds="http://opds-spec.org/">')
    ret += enc_print('<id>' + cfg.SITE_ID + '</id>')
    ret += enc_print('<title>' + cfg.SITE_TITLE + '</title>')
    ret += enc_print('<updated>' + time.strftime("%Y-%m-%dT%H:%M:%SZ") + '</updated>')
    ret += enc_print('<icon>' + cfg.SITE_ICON + '</icon>')
    ret += enc_print(
        '<author><name>' + cfg.SITE_AUTOR + '</name><uri>' + cfg.SITE_URL + '</uri><email>' + cfg.SITE_EMAIL + '</email></author>')
    #   ret += enc_print('<cover_show>'+str(cfg.COVER_SHOW)+'</cover_show>')
    return ret


def footer():
    return enc_print('</feed>')


def makeFeed():
    _author = dict(name=cfg.SITE_AUTOR, uri=cfg.SITE_URL, email=cfg.SITE_EMAIL)
    _feed = pyatom.OPDSAtomFeed(id=cfg.SITE_ID, title=cfg.SITE_TITLE, icon=cfg.SITE_ICON, author=_author)
    _feed.links.append(NavigationLink('/', rel='start', title=cfg.SITE_MAINTITLE).to_dict())
    return _feed


def add_previous_link(feed, id_value, page_value):
    feed.links.append(AsqusitionLink('/?id=' + id_value + '&amp;page=' + str(page_value - 1),
                                     rel='prev', title='Previous page').to_dict())


def add_next_link(feed, id_value, page_value):
    feed.links.append(AsqusitionLink('/?id=' + id_value + '&amp;page=' + str(page_value + 1),
                                     rel='next', title='Next page').to_dict())


###########################################################################################################
# Основной меню
#
def main_menu():
    dbinfo = opdsdb.getdbinfo(cfg.DUBLICATES_SHOW)
    _catalogs = dbinfo[2][0]
    _authors = dbinfo[1][0]
    _books = dbinfo[0][0]

    _feed = makeFeed()
    _feed.links.append(Link('opensearch.xml', type='application/opensearchdescription+xml', rel='search').to_dict())
    _feed.links.append(Link('/?search={searchTerms}', rel='search').to_dict())

    _link = NavigationLink('/?id=01')
    _entry = pyatom.FeedEntry(title='По каталогам', id='main:catalogs', content_type='text',
                              content='Каталогов: {0:d}, книг: {1:d}.'.format(_catalogs, _books),
                              links=[_link.to_dict()])
    _feed.add(_entry)

    _link = NavigationLink('/?id=02')
    _entry = pyatom.FeedEntry(title='По авторам', id='main:authors', content_type='text',
                              content='Авторов: {0:d}, книг: {1:d}.'.format(_authors, _books),
                              links=[_link.to_dict()])
    _feed.add(_entry)

    _link = NavigationLink('/?id=03')
    _entry = pyatom.FeedEntry(title='По наименованию', id='main:titles', content_type='text',
                              content='Авторов: {0:d}, книг: {1:d}.'.format(_authors, _books),
                              links=[_link.to_dict()])
    _feed.add(_entry)

    _link = NavigationLink('/?id=11')
    _entry = pyatom.FeedEntry(title='По жанрам', id='main:genres', content_type='text',
                              content='Авторов: {0:d}, книг: {1:d}.'.format(_authors, _books),
                              links=[_link.to_dict()])
    _feed.add(_entry)

    _link = NavigationLink('/?id=04')
    _entry = pyatom.FeedEntry(title='Последние добавленные', id='main:last', content_type='text',
                              content='Книг: {0:d}.'.format(min(cfg.MAXITEMS, _books)),
                              links=[_link.to_dict()])
    _feed.add(_entry)

    return _feed


def covers(cover, cover_type, book_id):
    have_extracted_cover = 0
    ret = ''
    if cfg.COVER_SHOW != 0:
        if cfg.COVER_SHOW != 2:
            if cover and cover != '':
                ret += enc_print(
                    '<link href="../covers/%s" rel="http://opds-spec.org/image" type="%s" />' % (cover, cover_type))
                ret += enc_print(
                    '<link href="../covers/%s" rel="x-stanza-cover-image" type="%s" />' % (cover, cover_type))
                ret += enc_print(
                    '<link href="../covers/%s" rel="http://opds-spec.org/thumbnail" type="%s" />' % (cover, cover_type))
                ret += enc_print(
                    '<link href="../covers/%s" rel="x-stanza-cover-image-thumbnail" type="%s" />' % (cover, cover_type))
                have_extracted_cover = 1
        if cfg.COVER_SHOW == 2 or (cfg.COVER_SHOW == 3 and have_extracted_cover == 0):
            _id = '99' + str(book_id)
            ret += enc_print('<link href="/?id=%s" rel="http://opds-spec.org/image" />' % (_id))
            ret += enc_print('<link href="/?id=%s" rel="x-stanza-cover-image" />' % (_id))
            ret += enc_print('<link href="/?id=%s" rel="http://opds-spec.org/thumbnail" />' % (_id))
            ret += enc_print('<link href="/?id=%s" rel="x-stanza-cover-image-thumbnail" />' % (_id))
    return ret


#########################################################
# Выбрана сортировка "По каталогам"
#
def list_of_catalogs(id_value, slice_value=0, page_value=0):
    _feed = makeFeed()
    if page_value > 0:
        add_previous_link(_feed, id_value, page_value)
    for (item_type, item_id, item_name, item_path, reg_date, item_title) in opdsdb.getitemsincat(slice_value,
                                                                                                 cfg.MAXITEMS,
                                                                                                 page_value):
        #logging.debug((item_type, item_id, item_name, item_path, reg_date, item_title))
        _authors = []
        if item_type == 1:
            _id = '01' + str(item_id)
        elif item_type == 2:
            _id = '07' + str(item_id)
            _authors = [dict(name=ln + ' ' + fn) for (fn, ln) in opdsdb.getauthors(item_id)]
        else:
            _id = '00'

        _entry = pyatom.FeedEntry(title=item_title or item_name,
                                  id='main:catalogs:' + str(item_id),
                                  updated=reg_date,
                                  content_type='text',
                                  content=', '.join([a['name'] for a in _authors]),
                                  author=_authors or [])
        _entry.links.append(AsqusitionLink('/?id=' + _id, rel='subsection').to_dict())
        _entry.links.append(Link('/?id=' + _id, rel='alternate').to_dict())
        _feed.entries.append(_entry)

    if opdsdb.next_page:
        add_next_link(_feed, id_value, page_value)
    return _feed


#########################################################
# Выбрана сортировка "По авторам" - выбор по несскольким первым буквам автора
#
def list_of_authors(id_value, slice_value):
    i = slice_value
    letter = ""
    while i > 0:
        letter = chr(i % 10000) + letter
        i //= 10000

    ret = enc_print(
        '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="' +
        cfg.SITE_MAINTITLE + '" href="/?id=00"/>')
    for (letters, cnt) in opdsdb.getauthor_2letters(letter):
        _id = ""
        for i in range(len(letters)):
            _id += '%04d' % (ord(letters[i]))

        if cfg.SPLITTITLES == 0 or cnt <= cfg.SPLITTITLES or len(letters) > 10:
            _id = '05' + _id
        else:
            _id = '02' + _id

        ret += enc_print('<entry>')
        ret += enc_print('<title>-= ' + websym(letters) + ' =-</title>')
        ret += enc_print('<id>/?id=' + id_value + '</id>')
        ret += enc_print('<link type="application/atom+xml" rel="alternate" href="/?id=' + _id + '"/>')
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="/?id='
            + _id + '"/>')
        ret += enc_print('<content type="text"> Всего: ' + str(cnt) + ' автора(ов).</content>')
        ret += enc_print('</entry>')
    return ret


#########################################################
# Выбрана сортировка "По наименованию" - выбор по нескольким первым буквам наименования
#
def list_of_title(id_value, slice_value):
    i = slice_value
    letter = ""
    while i > 0:
        letter = chr(i % 10000) + letter
        i = i // 10000

    ret = enc_print(
        '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'
        + cfg.SITE_MAINTITLE + '" href="/?id=00"/>')
    for (letters, cnt) in opdsdb.gettitle_2letters(letter, cfg.DUBLICATES_SHOW):
        _id = ''
        for i in range(len(letters)):
            _id += '%04d' % (ord(letters[i]))

        if cfg.SPLITTITLES == 0 or cnt <= cfg.SPLITTITLES or len(letters) > 10:
            _id = '10' + _id
        else:
            _id = '03' + _id

        ret += enc_print('<entry>')
        ret += enc_print('<title>-= ' + websym(letters) + ' =-</title>')
        ret += enc_print('<id>/?id=' + id_value + '</id>')
        ret += enc_print('<link type="application/atom+xml" rel="alternate" href="/?id=' + _id + '"/>')
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="/?id=' + _id + '"/>')
        ret += enc_print('<content type="text"> Всего: ' + str(cnt) + ' наименований.</content>')
        ret += enc_print('</entry>')
    return ret


#########################################################
# Выдача списка книг по наименованию или на основании поискового запроса
#
def list_of_title_or_search(id_value, slice_value, page_value, searchTerm):
    if slice_value >= 0:
        i = slice_value
        letter = ""
        while i > 0:
            letter = chr(i % 10000) + letter
            i //= 10000
    else:
        letter = "%" + searchTerm
    ret = ''
    for (book_id, book_name, book_path, reg_date, book_title, cover, cover_type) in \
            opdsdb.getbooksfortitle(letter, cfg.MAXITEMS, page_value, cfg.DUBLICATES_SHOW):
        _id = '07' + str(book_id)
        ret += enc_print('<entry>')
        ret += enc_print('<title>' + websym(book_title) + '</title>')
        ret += enc_print('<updated>' + reg_date.strftime("%Y-%m-%dT%H:%M:%SZ") + '</updated>')
        ret += enc_print('<id>/?id=' + _id + '</id>')
        ret += covers(cover, cover_type, book_id)
        ret += enc_print('<link type="application/atom+xml" rel="alternate" href="/?id=' + _id + '"/>')
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="/?id='
            + _id + '"/>')
        authors = ""
        for (first_name, last_name) in opdsdb.getauthors(book_id):
            ret += enc_print('<author><name>' + last_name + ' ' + first_name + '</name></author>')
            if len(authors) > 0:
                authors += ', '
            authors += last_name + ' ' + first_name
        ret += enc_print('<content type="text">' + authors + '</content>')
        ret += enc_print('</entry>')
    if page_value > 0:
        prev_href = "/?id=" + id_value + "&amp;page=" + str(page_value - 1)
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="prev" title="Previous Page" href="'
            + prev_href + '" />')
    if opdsdb.next_page:
        next_href = "/?id=" + id_value + "&amp;page=" + str(page_value + 1)
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="next" title="Next Page" href="'
            + next_href + '" />')
    return ret


#########################################################
# Выбрана сортировка "По жанрам" - показ секций
#
def list_of_genre(id_value):
    ret = enc_print(
        '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'
        + cfg.SITE_MAINTITLE + '" href="/?id=00"/>')
    for (genre_id, genre_section, cnt) in opdsdb.getgenres_sections():
        _id = '12' + str(genre_id)
        enc_print('<entry>')
        enc_print('<title>' + genre_section + '</title>')
        enc_print('<id>/?id=' + id_value + '</id>')
        enc_print('<link type="application/atom+xml" rel="alternate" href="/?id=' + _id + '"/>')
        enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="/?id='
            + _id + '"/>')
        enc_print('<content type="text"> Всего: ' + str(cnt) + ' книг.</content>')
        enc_print('</entry>')
    return ret


#########################################################
# Выбрана сортировка "По жанрам" - показ подсекций
#
def list_of_genre_subsections(id_value, slice_value):
    ret = enc_print(
        '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'
        + cfg.SITE_MAINTITLE + '" href="/?id=00"/>')
    for (genre_id, genre_subsection, cnt) in opdsdb.getgenres_subsections(slice_value):
        _id = '13' + str(genre_id)
        ret += enc_print('<entry>')
        ret += enc_print('<title>' + genre_subsection + '</title>')
        ret += enc_print('<id>/?id=' + id_value + '</id>')
        ret += enc_print('<link type="application/atom+xml" rel="alternate" href="/?id=' + _id + '"/>')
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="/?id='
            + _id + '"/>')
        ret += enc_print('<content type="text"> Всего: ' + str(cnt) + ' книг.</content>')
        ret += enc_print('</entry>')
    return ret


#########################################################
# Выдача списка книг по жанру
#
def list_of_subsection(id_value, slice_value, page_value):
    ret = ''
    for (book_id, book_name, book_path, reg_date, book_title, cover, cover_type) in \
            opdsdb.getbooksforgenre(slice_value, cfg.MAXITEMS, page_value, cfg.DUBLICATES_SHOW):
        _id = '07' + str(book_id)
        ret += enc_print('<entry>')
        ret += enc_print('<title>' + websym(book_title) + '</title>')
        ret += enc_print('<updated>' + reg_date.strftime("%Y-%m-%dT%H:%M:%SZ") + '</updated>')
        ret += enc_print('<id>/?id=' + _id + '</id>')
        ret += covers(cover, cover_type, book_id)
        ret += enc_print('<link type="application/atom+xml" rel="alternate" href="/?id=' + _id + '"/>')
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="/?id='
            + _id + '"/>')
        authors = ""
        for (first_name, last_name) in opdsdb.getauthors(book_id):
            ret += enc_print('<author><name>' + last_name + ' ' + first_name + '</name></author>')
            if len(authors) > 0:
                authors += ', '
            authors += last_name + ' ' + first_name
        ret += enc_print('<content type="text">' + authors + '</content>')
        ret += enc_print('</entry>')
    if page_value > 0:
        prev_href = "/?id=" + id_value + "&amp;page=" + str(page_value - 1)
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="prev" title="Previous Page" href="'
            + prev_href + '" />')
    if opdsdb.next_page:
        next_href = "/?id=" + id_value + "&amp;page=" + str(page_value + 1)
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="next" title="Next Page" href="'
            + next_href + '" />')
    return ret


#########################################################
# Выбрана сортировка "Последние поступления"
#
def list_of_last():
    ret = ''
    for (book_id, book_name, book_path, reg_date, book_title) in opdsdb.getlastbooks(cfg.MAXITEMS):
        _id = '07' + str(book_id)
        ret += enc_print('<entry>')
        ret += enc_print('<title>' + websym(book_title) + '</title>')
        ret += enc_print('<updated>' + reg_date.strftime("%Y-%m-%dT%H:%M:%SZ") + '</updated>')
        ret += enc_print('<id>/?id=04</id>')
        ret += enc_print('<link type="application/atom+xml" rel="alternate" href="/?id=' + _id + '"/>')
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="/?id='
            + _id + '"/>')
        authors = ""
        for (first_name, last_name) in opdsdb.getauthors(book_id):
            ret += enc_print('<author><name>' + last_name + ' ' + first_name + '</name></author>')
            if len(authors) > 0:
                authors += ', '
            authors += last_name + ' ' + first_name
        ret += enc_print('<content type="text">' + authors + '</content>')
        ret += enc_print('</entry>')
    return ret


#########################################################
# Выдача списка авторов
#
def list_authors(id_value, slice_value, page_value):
    i = slice_value
    letter = ""
    while i > 0:
        letter = chr(i % 10000) + letter
        i = i // 10000

    ret = enc_print(
        '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'
        + cfg.SITE_MAINTITLE + '" href="/?id=00"/>')
    for (author_id, first_name, last_name, cnt) in opdsdb.getauthorsbyl(letter, cfg.MAXITEMS, page_value,
                                                                        cfg.DUBLICATES_SHOW):
        _id = '06' + str(author_id)
        ret += enc_print('<entry>')
        ret += enc_print('<title>' + last_name + ' ' + first_name + '</title>')
        ret += enc_print('<id>/?id=' + id_value + '</id>')
        ret += enc_print('<link type="application/atom+xml" rel="alternate" href="/?id=' + _id + '"/>')
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="/?id='
            + _id + '"/>')
        ret += enc_print('<content type="text"> Всего: ' + str(cnt) + ' книг.</content>')
        ret += enc_print('</entry>')
    if page_value > 0:
        prev_href = "/?id=" + id_value + "&amp;page=" + str(page_value - 1)
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="prev" title="Previous Page" href="'
            + prev_href + '" />')
    if opdsdb.next_page:
        next_href = "/?id=" + id_value + "&amp;page=" + str(page_value + 1)
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="next" title="Next Page" href="'
            + next_href + '" />')
    return ret


#########################################################
# Выдача списка книг по автору
#
def list_book_of_author(id_value, slice_value, page_value):
    ret = ''
    for (book_id, book_name, book_path, reg_date, book_title, cover, cover_type) in \
            opdsdb.getbooksforautor(slice_value, cfg.MAXITEMS, page_value, cfg.DUBLICATES_SHOW):
        _id = '07' + str(book_id)
        ret += enc_print('<entry>')
        ret += enc_print('<title>' + websym(book_title) + '</title>')
        ret += enc_print('<updated>' + reg_date.strftime("%Y-%m-%dT%H:%M:%SZ") + '</updated>')
        ret += enc_print('<id>/?id=' + _id + '</id>')
        ret += covers(cover, cover_type, book_id)
        ret += enc_print('<link type="application/atom+xml" rel="alternate" href="/?id=' + _id + '"/>')
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="/?id='
            + _id + '"/>')
        authors = ""
        for (first_name, last_name) in opdsdb.getauthors(book_id):
            ret += enc_print('<author><name>' + last_name + ' ' + first_name + '</name></author>')
            if len(authors) > 0:
                authors += ', '
            authors += last_name + ' ' + first_name
        ret += enc_print('<content type="text">' + authors + '</content>')
        ret += enc_print('</entry>')
    if page_value > 0:
        prev_href = "/?id=" + id_value + "&amp;page=" + str(page_value - 1)
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="prev" title="Previous Page" href="'
            + prev_href + '" />')
    if opdsdb.next_page:
        next_href = "/?id=" + id_value + "&amp;page=" + str(page_value + 1)
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="next" title="Next Page" href="'
            + next_href + '" />')
    return ret


#########################################################
# Выдача ссылок на книгу
#
def list_of_ref(id_value, book_id):
    _feed = makeFeed()
    _feed.links.append(AsqusitionLink('/?id=07' + str(book_id), rel='self').to_dict())
    #    (book_name, book_path, reg_date, _format, title, cat_type, cover, cover_type, file_size) = opdsdb.getbook(
    #        slice_value)
    book = opdsdb._getbook(book_id)
    if book:
        authors = [dict(name=author.last_name + ' ' + author.first_name) for author in book.authors]
        _content = 'Название книги: {0:s}\nАвтор(ы): {1:s}\nЖанры: {2:s}\nРазмер файла : {3:d} Кб'. \
            format(book.title, ', '.join([author['name'] for author in authors]),
                   ', '.join([genre.subsection for genre in book.genres]), book.filesize // 1000)
        _entry = pyatom.FeedEntry(title='Файл: ' + book.filename,
                                  id='main:book:' + str(book_id),
                                  updated=book.registerdate,
                                  author=authors or [],
                                  content_type='text',
                                  content=_content)
        _entry.links.append(
            Link('/?id=08' + str(book_id), _type='application/' + book.format, rel='alternate').to_dict())
        _entry.links.append(Link('/?id=08' + str(book_id), _type='application/' + book.format,
                                 rel='http://opds-spec.org/acquisition').to_dict())
        _entry.links.append(Link('/?id=09' + str(book_id), _type='application/' + book.format + '+zip',
                                 rel='http://opds-spec.org/acquisition').to_dict())
        _feed.add(_entry)

        #    ret += covers(cover, cover_type, slice_value)

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
    book = opdsdb._getbook(book_id)
    full_path = os.path.join(cfg.ROOT_LIB, book.path)
    # HTTP Header
    headers = [('Content-Type', 'application/octet-stream; name="' + book.filename + '"'),
               ('Content-Disposition', 'attachment; filename=' + translit(book.filename)),
               ('Content-Transfer-Encoding', 'binary')]
    if book.cat_type == sopdsdb.CAT_NORMAL:
        file_path = os.path.join(full_path, book.filename)
        book_size = os.path.getsize(file_path.encode('utf-8'))
        headers.append(('Content-Length', str(book_size)))
        fo = open(file_path, "rb")
        ret = fo.read()
        fo.close()
    elif book.cat_type == sopdsdb.CAT_ZIP:
        z = zipfile.ZipFile(full_path, 'r', allowZip64=True)
        book_size = z.getinfo(book.filename).file_size
        headers.append(('Content-Length', str(book_size)))
        fo = z.open(book.filename)
        ret = fo.read()
        fo.close()
        z.close()
    return headers, ret


#########################################################
# Выдача файла книги в ZIP формате
#
def out_zipfile_of_book():
    return ''
    # (book_name, book_path, reg_date, format, title, cat_type, cover, cover_type, fsize) = opdsdb.getbook(slice_value)
    # full_path = os.path.join(cfg.ROOT_LIB, book_path)
    # transname = translit(book_name)
    # # HTTP Header
    # enc_print('Content-Type:application/zip; name="' + book_name + '"')
    # enc_print("Content-Disposition: attachment; filename=" + transname + '.zip')
    # enc_print('Content-Transfer-Encoding: binary')
    # if cat_type == sopdsdb.CAT_NORMAL:
    #     file_path = os.path.join(full_path, book_name)
    #     dio = io.BytesIO()
    #     z = zipf.ZipFile(dio, 'w', zipf.ZIP_DEFLATED)
    #     z.write(file_path.encode('utf-8'), transname)
    #     z.close()
    #     buf = dio.getvalue()
    #     enc_print('Content-Length: %s' % len(buf))
    #     enc_print()
    #     sys.stdout.buffer.write(buf)
    # elif cat_type == sopdsdb.CAT_ZIP:
    #     fz = codecs.open(full_path.encode("utf-8"), "rb")
    #     zi = zipf.ZipFile(fz, 'r', allowZip64=True, codepage=cfg.ZIP_CODEPAGE)
    #     fo = zi.open(book_name)
    #     str = fo.read()
    #     fo.close()
    #     zi.close()
    #     fz.close()
    #
    #     dio = io.BytesIO()
    #     zo = zipf.ZipFile(dio, 'w', zipf.ZIP_DEFLATED)
    #     zo.writestr(transname, str)
    #     zo.close()
    #
    #     buf = dio.getvalue()
    #     enc_print('Content-Length: %s' % len(buf))
    #     enc_print()
    #     sys.stdout.buffer.write(buf)
    #
    # opdsdb.closeDB()


#########################################################
# Выдача Обложки На лету
#
def get_cover():
    return ''
    # (book_name, book_path, reg_date, format, title, cat_type, cover, cover_type, fsize) = opdsdb.getbook(slice_value)
    # c0 = 0
    # if format == 'fb2':
    #     full_path = os.path.join(cfg.ROOT_LIB, book_path)
    #     fb2 = sopdsparse.fb2parser(1)
    #     if cat_type == sopdsdb.CAT_NORMAL:
    #         file_path = os.path.join(full_path, book_name)
    #         fo = codecs.open(file_path.encode("utf-8"), "rb")
    #         fb2.parse(fo, 0)
    #         fo.close()
    #     elif cat_type == sopdsdb.CAT_ZIP:
    #         fz = codecs.open(full_path.encode("utf-8"), "rb")
    #         z = zipf.ZipFile(fz, 'r', allowZip64=True, codepage=cfg.ZIP_CODEPAGE)
    #         fo = z.open(book_name)
    #         fb2.parse(fo, 0)
    #         fo.close()
    #         z.close()
    #         fz.close()
    #
    #     if len(fb2.cover_image.cover_data) > 0:
    #         try:
    #             s = fb2.cover_image.cover_data
    #             dstr = base64.b64decode(s)
    #             ictype = fb2.cover_image.getattr('content-type')
    #             enc_print('Content-Type:' + ictype)
    #             enc_print()
    #             sys.stdout.buffer.write(dstr)
    #             c0 = 1
    #         except:
    #             c0 = 0
    #
    # if c0 == 0:
    #     if os.path.exists(sopdscfg.NOCOVER_IMG):
    #         enc_print('Content-Type: image/jpeg')
    #         enc_print()
    #         f = open(sopdscfg.NOCOVER_IMG, "rb")
    #         sys.stdout.buffer.write(f.read())
    #         f.close()
    #     else:
    #         print('Status: 404 Not Found')
    #         print()


import pyatom


def simple_app(environ, start_response):
    d = parse_qs(environ['QUERY_STRING'])

    logging.debug(d)

    type_value = 0
    slice_value = 0
    page_value = 0

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
        searchTerm = d.get('search', [''])[0]
        type_value = 10
        slice_value = -1
        id_value = "10&amp;search=" + searchTerm

    status = '200 OK'g
    headers = [('Content-type', 'text/xml; charset=utf-8')]

    if type_value == 0:
        feed = main_menu()
        logging.debug(feed)
        ret = [feed.to_bytestring()]
    elif type_value == 1:
        feed = list_of_catalogs(id_value, slice_value, page_value)
        logging.debug(feed)
        ret = [feed.to_bytestring()]
    elif type_value == 2:
        ret = [header().encode('utf-8'),
               list_of_authors(id_value, slice_value).encode('utf-8'),
               footer().encode('utf-8')]
    elif type_value == 3:
        ret = [header().encode('utf-8'),
               list_of_title(id_value, slice_value).encode('utf-8'),
               footer().encode('utf-8')]
    elif type_value == 10:
        ret = [header().encode('utf-8'),
               list_of_title_or_search(id_value, slice_value, page_value, searchTerm).encode('utf-8'),
               footer().encode('utf-8')]
    elif type_value == 11:
        ret = [header().encode('utf-8'),
               list_of_genre(id_value).encode('utf-8'),
               footer().encode('utf-8')]
    elif type_value == 12:
        ret = [header().encode('utf-8'),
               list_of_genre_subsections(id_value, slice_value).encode('utf-8'),
               footer().encode('utf-8')]
    elif type_value == 13:
        ret = [header().encode('utf-8'),
               list_of_subsection(id_value, slice_value, page_value).encode('utf-8'),
               footer().encode('utf-8')]
    elif type_value == 4:
        ret = [header().encode('utf-8'),
               list_of_last().encode('utf-8'),
               footer().encode('utf-8')]
    elif type_value == 5:
        ret = [header().encode('utf-8'),
               list_authors(id_value, slice_value, page_value).encode('utf-8'),
               footer().encode('utf-8')]
    elif type_value == 6:
        ret = [header().encode('utf-8'),
               list_book_of_author(id_value, slice_value, page_value).encode('utf-8'),
               footer().encode('utf-8')]
    elif type_value == 7:
        feed = list_of_ref(id_value, slice_value)
        logging.debug(feed)
        ret = [feed.to_bytestring()]
    elif type_value == 8:
        headers, ret = out_file_of_book(slice_value)
        ret = [ret]
    elif type_value == 9:
        ret = [header().encode('utf-8'),
               out_zipfile_of_book().encode('utf-8'),
               footer().encode('utf-8')]
    elif type_value == 99:
        ret = [header().encode('utf-8'),
               get_cover().encode('utf-8'),
               footer().encode('utf-8')]
    else:
        ret = [header().encode('utf-8'),
               footer().encode('utf-8')]

    start_response(status, headers)
    return ret


if __name__ == '__main__':
    logging.basicConfig(filename='server.log', level=logging.DEBUG)

    opdsdb = sopdsdb.opdsDatabase(cfg.ENGINE + cfg.DB_NAME, cfg.DB_USER, cfg.DB_PASS, cfg.DB_HOST, cfg.ROOT_LIB)
    opdsdb.openDB()

    validator_app = validator(simple_app)
    httpd = make_server('', cfg.PORT, validator_app)
    print('Serving on port {0:d}...'.format(cfg.PORT))
    httpd.serve_forever()

    opdsdb.closeDB()
