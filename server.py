# -*- coding: utf-8 -*-
__author__ = 'vseklecov'

import codecs
import os
from urllib.parse import parse_qs
import time
from wsgiref.validate import validator
from wsgiref.simple_server import make_server

import db as sopdsdb


class Config():
    SITE_ID = ''
    SITE_ICON = ''
    SITE_TITLE = ''
    SITE_AUTOR = ''
    SITE_URL = ''
    SITE_EMAIL = ''
    SITE_MAINTITLE = ''
    DB_NAME = 'sqlite:///:memory:'
    DB_USER = ''
    DB_PASS = ''
    DB_HOST = ''

    ROOT_LIB = ''
    DUBLICATES_SHOW = 0
    MAXITEMS = 10
    SPLITTITLES = 0
    COVER_SHOW = 0

cfg = Config()


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


###########################################################################################################
# Основной меню
#
def main_menu():
    dbinfo = opdsdb.getdbinfo(cfg.DUBLICATES_SHOW)
    ret = enc_print(
        '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="' + cfg.SITE_MAINTITLE + '" href="/"/>')
    ret += enc_print('<link href="opensearch.xml" rel="search" type="application/opensearchdescription+xml" />')
    ret += enc_print('<link href="/?search={searchTerms}" rel="search" type="application/atom+xml" />')
    ret += enc_print('<entry>')
    ret += enc_print('<title>По каталогам</title>')
    ret += enc_print('<content type="text">Каталогов: %s, книг: %s.</content>' % (dbinfo[2][0], dbinfo[0][0]))
    ret += enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="/?id=01"/>')
    ret += enc_print('<id>/?id=1</id></entry>')
    ret += enc_print('<entry>')
    ret += enc_print('<title>По авторам</title>')
    ret += enc_print('<content type="text">Авторов: %s, книг: %s.</content>' % (dbinfo[1][0], dbinfo[0][0]))
    ret += enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="/?id=02"/>')
    ret += enc_print('<id>/?id=2</id></entry>')
    ret += enc_print('<entry>')
    ret += enc_print('<title>По наименованию</title>')
    ret += enc_print('<content type="text">Авторов: %s, книг: %s.</content>' % (dbinfo[1][0], dbinfo[0][0]))
    ret += enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="/?id=03"/>')
    ret += enc_print('<id>/?id=10</id></entry>')
    ret += enc_print('<entry>')
    ret += enc_print('<title>По Жанрам</title>')
    ret += enc_print('<content type="text">Авторов: %s, книг: %s.</content>' % (dbinfo[1][0], dbinfo[0][0]))
    ret += enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="/?id=11"/>')
    ret += enc_print('<id>/?id=11</id></entry>')
    ret += enc_print('<entry>')
    ret += enc_print('<title>Последние добавленные</title>')
    ret += enc_print('<content type="text">Книг: %s.</content>' % (cfg.MAXITEMS))
    ret += enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="/?id=04"/>')
    ret += enc_print('<id>/?id=4</id></entry>')
    return ret


def covers(cover, cover_type, book_id):
    have_extracted_cover = 0
    ret = ''
    if cfg.COVER_SHOW != 0:
        if cfg.COVER_SHOW != 2:
            if cover and cover != '':
                ret += enc_print(
                    '<link href="../covers/%s" rel="http://opds-spec.org/image" type="%s" />' % (cover, cover_type))
                ret += enc_print('<link href="../covers/%s" rel="x-stanza-cover-image" type="%s" />' % (cover, cover_type))
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
def list_of_catlogs(id_value, slice_value, page_value):
    ret = enc_print(
        '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'
        + cfg.SITE_MAINTITLE + '" href="/?id=0"/>')
    for (item_type, item_id, item_name, item_path, reg_date, item_title) in opdsdb.getitemsincat(slice_value,
                                                                                                 cfg.MAXITEMS,
                                                                                                 page_value):
        if item_type == 1:
            id = '01' + str(item_id)
        elif item_type == 2:
            id = '07' + str(item_id)
        else:
            id = '00'
        ret += enc_print('<entry>')
        ret += enc_print('<title>' + item_title + '</title>')
        ret += enc_print('<updated>' + reg_date.strftime("%Y-%m-%dT%H:%M:%SZ") + '</updated>')
        ret += enc_print('<id>/?id=00</id>')
        ret += enc_print('<link type="application/atom+xml" rel="alternate" href="/?id=' + id + '"/>')
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="/?id='
            + id + '"/>')
        if item_type == 2:
            authors = ""
            for (first_name, last_name) in opdsdb.getauthors(item_id):
                ret += enc_print('<author><name>' + last_name + ' ' + first_name + '</name></author>')
                if len(authors) > 0:
                    authors += ', '
                authors += last_name + ' ' + first_name
            ret += enc_print('<content type="text">' + authors + '</content>')
        ret += enc_print('</entry>')
    if page_value > 0:
        prev_href = "/?id=" + id_value + "&amp;page=" + str(page_value - 1)
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="prev" title="Previous Page" href="' + prev_href + '" />')
    if opdsdb.next_page:
        next_href = "/?id=" + id_value + "&amp;page=" + str(page_value + 1)
        ret += enc_print(
            '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="next" title="Next Page" href="' + next_href + '" />')
    return ret


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
    for (book_id, book_name, book_path, reg_date, book_title, cover, cover_type) in\
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
    for (book_id, book_name, book_path, reg_date, book_title, cover, cover_type) in\
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
def list_of_ref(id_value, slice_value):
    _id = '07' + str(slice_value)
    ret = enc_print(
        '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" href="/?id=0" title="'
        + cfg.SITE_MAINTITLE + '"/>')
    ret += enc_print(
        '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="self" href="/?id=' + _id + '"/>')
    (book_name, book_path, reg_date, format, title, cat_type, cover, cover_type, fsize) = opdsdb.getbook(slice_value)
    _id = '08' + str(slice_value)
    idzip = '09' + str(slice_value)
    ret += enc_print('<entry>')
    ret += enc_print('<title>Файл: ' + book_name + '</title>')
    ret += covers(cover, cover_type, slice_value)
    ret += enc_print('<link type="application/' + format + '" rel="alternate" href="/?id=' + _id + '"/>')
    ret += enc_print(
        '<link type="application/' + format + '" href="/?id=' + _id + '" rel="http://opds-spec.org/acquisition" />')
    ret += enc_print(
        '<link type="application/' + format + '+zip" href="/?id='
        + idzip + '" rel="http://opds-spec.org/acquisition" />')
    authors = ""
    for (first_name, last_name) in opdsdb.getauthors(slice_value):
        ret += enc_print('<author><name>' + last_name + ' ' + first_name + '</name></author>')
        if len(authors) > 0:
            authors += ', '
        authors += last_name + ' ' + first_name
    genres = ""
    for (section, genre) in opdsdb.getgenres(slice_value):
        ret += enc_print('<category term="%s" label="%s" />' % (genre, genre))
        if len(genres) > 0:
            genres += ', '
        genres += genre

    ret += enc_print(
        '<content type="text"> Название книги: ' + title + '\nАвтор(ы): ' + authors + '\nЖанры: ' +
        genres + '\nРазмер файла : ' + str(fsize // 1000) + 'Кб</content>')

    ret += enc_print('<updated>' + reg_date.strftime("%Y-%m-%dT%H:%M:%SZ") + '</updated>')
    ret += enc_print('<id>tag:book:' + _id + '</id>')
    ret += enc_print('</entry>')
    return ret


#########################################################
# Выдача файла книги
#
def out_file_of_book(slice_value):
    return ''
    (book_name, book_path, reg_date, format, title, cat_type, cover, cover_type, fsize) = opdsdb.getbook(slice_value)
    full_path = os.path.join(cfg.ROOT_LIB, book_path)
    transname = translit(book_name)
    # HTTP Header
    head = enc_print('Content-Type:application/octet-stream; name="' + book_name + '"')
    head += enc_print("Content-Disposition: attachment; filename=" + transname)
    head += enc_print('Content-Transfer-Encoding: binary')
    if cat_type == sopdsdb.CAT_NORMAL:
        file_path = os.path.join(full_path, book_name)
        book_size = os.path.getsize(file_path.encode('utf-8'))
        head += enc_print('Content-Length: ' + str(book_size))
        head += enc_print()
        fo = codecs.open(file_path.encode("utf-8"), "rb")
        string = fo.read()
        sys.stdout.buffer.write(string)
        fo.close()
    elif cat_type == sopdsdb.CAT_ZIP:
        # fz = codecs.open(full_path.encode("utf-8"), "rb")
        # z = zipf.ZipFile(fz, 'r', allowZip64=True, codepage=cfg.ZIP_CODEPAGE)
        # book_size = z.getinfo(book_name).file_size
        # enc_print('Content-Length: ' + str(book_size))
        # enc_print()
        # fo = z.open(book_name)
        # str = fo.read()
        # sys.stdout.buffer.write(str)
        # fo.close()
        # z.close()
        # fz.close()
        pass


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


def simple_app(environ, start_response):
    d = parse_qs(environ['QUERY_STRING'])

    print(d)

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

    status = '200 OK'
    headers = [('Content-type', 'text/xml; charset=utf-8')]
    start_response(status, headers)

    if type_value == 0:
        ret = [header().encode('utf-8'),
               main_menu().encode('utf-8'),
               footer().encode('utf-8')]
    elif type_value == 1:
        ret = [header().encode('utf-8'),
               list_of_catlogs(id_value, slice_value, page_value).encode('utf-8'),
               footer().encode('utf-8')]
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
               list_of_authors(id_value, slice_value).encode('utf-8'),
               footer().encode('utf-8')]
    elif type_value == 6:
        ret = [header().encode('utf-8'),
               list_book_of_author(id_value, slice_value, page_value).encode('utf-8'),
               footer().encode('utf-8')]
    elif type_value == 7:
        ret = [header().encode('utf-8'),
               list_of_ref(id_value, slice_value).encode('utf-8'),
               footer().encode('utf-8')]
    elif type_value == 8:
        ret = [header().encode('utf-8'),
               out_file_of_book(slice_value).encode('utf-8'),
               footer().encode('utf-8')]
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

    print(ret)
    return ret


opdsdb = sopdsdb.opdsDatabase(cfg.DB_NAME, cfg.DB_USER, cfg.DB_PASS, cfg.DB_HOST, cfg.ROOT_LIB)
opdsdb.openDB()
opdsdb.init_db()
opdsdb.addcattree('C:/TEMP/TEXT/BOOK')

validator_app = validator(simple_app)
httpd = make_server('', 8000, validator_app)
print("Serving on port 8000...")
httpd.serve_forever()

opdsdb.closeDB()
