# -*- coding: utf-8 -*-
__author__ = 'vseklecov'

UNKNOWN_GENRE = 'Неизвестный жанр'
UNKNOWN_AUTHOR = 'Неизвестный автор'

import os

from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sql
import sqlalchemy.orm as orm

Base = declarative_base()

book_authors = sql.Table('bauthors',
                         Base.metadata,
                         sql.Column('author_id', sql.ForeignKey('authors.author_id')),
                         sql.Column('book_id', sql.ForeignKey('books.book_id')), sql.PrimaryKeyConstraint('author_id', 'book_id'))

book_genre = sql.Table('bgenres',
                       Base.metadata,
                       sql.Column('genre_id', sql.Integer, sql.ForeignKey('genres.genre_id')),
                       sql.Column('book_id', sql.Integer, sql.ForeignKey('books.book_id')))


class Book(Base):
    __tablename__ = 'books'

    book_id = sql.Column(sql.Integer, sql.Sequence('book_id_seq'), primary_key=True)
    filename = sql.Column(sql.String(256), index=True)
    path = sql.Column(sql.String(1024))
    filesize = sql.Column(sql.Integer, nullable=False, default=0)
    format = sql.Column(sql.String(8))
    cat_id = sql.Column(sql.Integer, sql.ForeignKey('catalogs.cat_id'), nullable=False)
    cat_type = sql.Column(sql.Integer, nullable=False, default=0)
    registerdate = sql.Column(sql.DateTime, default=sql.func.now())
    favorite = sql.Column(sql.Integer, nullable=False, default=0)
    lang = sql.Column(sql.String(16))
    title = sql.Column(sql.String(256), index=True)
    cover = sql.Column(sql.String(32))
    cover_type = sql.Column(sql.String(32))
    doublicat = sql.Column(sql.Integer, nullable=False, default=0)

    authors = orm.relationship('Author', secondary=book_authors, backref='books')
    genres = orm.relationship('Genre', secondary=book_genre, backref='books')

    def __init__(self, name, path, cat_id, size, format_book, title, lang, archive, doublicat):
        self.filename = name
        self.path = path
        self.cat_id = cat_id
        self.filesize = size
        self.format = format_book
        self.title = title
        self.lang = lang
        self.cat_type = archive
        self.doublicat = doublicat

    def __repr__(self):
        return "<Book('%s','%s')>" % (self.title, ','.join(self.authors))


class Catalog(Base):
    __tablename__ = 'catalogs'

    cat_id = sql.Column(sql.Integer, sql.Sequence('cat_id_seq'), primary_key=True)
    parent_id = sql.Column(sql.Integer, nullable=True)
    cat_name = sql.Column(sql.String(64), index=True)
    path = sql.Column(sql.String(1024))
    cat_type = sql.Column(sql.Integer, nullable=False, default=0)

    books = orm.relationship('Book', backref='catalog')

    def __init__(self, parent_id, cat_name, path, cat_type):
        self.parent_id = parent_id
        self.cat_name = cat_name
        self.path = path
        self.cat_type = cat_type

    def __repr__(self):
        return "<Catalog('%s')>" % self.cat_name


class Author(Base):
    __tablename__ = 'authors'

    author_id = sql.Column(sql.Integer, sql.Sequence('author_id_seq'), primary_key=True)
    first_name = sql.Column(sql.String(64))
    last_name = sql.Column(sql.String(64))
    search_name = sql.Column(sql.String(128), index=True)

    def __init__(self, last_name, first_name=''):
        self.last_name = last_name
        self.first_name = first_name
        self.search_name = last_name.lower()+' '+first_name.lower()

    def __repr__(self):
        return "<Author('%s %s')>" % (self.last_name, self.first_name)


class Genre(Base):
    __tablename__ = 'genres'

    genre_id = sql.Column(sql.Integer, sql.Sequence('genre_id_seq'), primary_key=True)
    genre = sql.Column(sql.String(32))
    section = sql.Column(sql.String(32))
    subsection = sql.Column(sql.String(64))

    sql.Index('genre', genre)

    def __init__(self, genre, subsection, section):
        self.genre = genre
        self.section = section
        self.subsection = subsection

    def __repr__(self):
        return "<Genre(%s)>" % self.subsection


class opdsDatabase:
    def __init__(self, iname='sqlite:///:memory:', iuser='', ipass='', ihost='localhost', iroot_lib='..'):
        self.db_name = iname
        self.db_user = iuser
        self.db_pass = ipass
        self.db_host = ihost
        self.root_lib = iroot_lib

        self.errcode = 0
        self.err = ''
        self.isopen = False
        self.next_page = False

    def openDB(self):
        if not self.isopen:
            try:
                self.engine = sql.create_engine(self.db_name)
                Session = orm.sessionmaker(bind=self.engine)
                self.session = Session()
            except:
                self.err = ''
                self.errcode = 1
            else:
                self.isopen = True
        else:
            self.errcode = 1
            self.err = 'Error open database. Database already open.'

    def closeDB(self):
        if self.isopen:
            self.session.close()
            self.isopen = False
        else:
            self.errcode = 5
            self.err = 'Attempt to close not opened database.'

    def printDBerr(self):
        if self.errcode == 0:
            print("No database error found.")
        else:
            print("Error code =", self.errcode, ".Error message:", self.err)

    def clearDBerr(self):
        self.err = ''
        self.errcode = 0

    def findbook(self, name, path):
        book = self.session.query(Book). \
            filter(Book.filename == name, Book.path == path).order_by(Book.book_id).first()
        if not book:
            book_id = 0
        else:
            book_id = book.book_id
        return book_id

    def finddouble(self, title, format_book, file_size):
        book = self.session.query(Book). \
            filter(Book.title == title, Book.format == format_book, Book.filesize == file_size, Book.doublicat == 0). \
            order_by(Book.book_id).first()
        if not book:
            book_id = 0
        else:
            book_id = book.book_id
        return book_id

    def addbook(self, name, path, cat_id, exten, title, lang, size=0, archive=0, doublicates=0):
        book_id = self.findbook(name, path)
        if book_id != 0:
            return book_id
        format_book = exten[1:]
        format_book = format_book.lower()
        if doublicates != 0:
            doublicat = self.finddouble(title, format_book, size)
        else:
            doublicat = 0
        book = Book(name, path, cat_id, size, format_book, title, lang, archive, doublicat)
        self.session.add(book)
        self.session.commit()
        return book.book_id

    def addcover(self, book_id, fn, cover_type):
        try:
            book = self.session.query(Book).filter(Book.book_id == book_id).one()
        except:
            return
        book.cover = fn
        book.cover_type = cover_type
        self.session.commit()

    def findauthor(self, first_name, last_name):
        search_name = last_name.lower()+' '+first_name.lower()
        author = self.session.query(Author).filter(Author.search_name == search_name).first()
        if not author:
            author_id = 0
        else:
            author_id = author.author_id
        return author_id

    def findbauthor(self, book_id, author_id):
        try:
            book = self.session.query(Book).filter(Book.book_id == book_id).one()
            author = self.session.query(Author).filter(Author.author_id == author_id).one()
        except orm.exc.NoResultFound:
            return False
        result = author in book.authors
        return result

    def addauthor(self, first_name, last_name):
        author_id = self.findauthor(first_name, last_name)
        if author_id != 0:
            return author_id
        author = Author(last_name, first_name)
        self.session.add(author)
        self.session.commit()
        return author.author_id

    def addbauthor(self, book_id, author_id):
        try:
            book = self.session.query(Book).filter(Book.book_id == book_id).one()
            author = self.session.query(Author).filter(Author.author_id == author_id).one()
        except orm.exc.NoResultFound:
            return
        book.authors.append(author)
        self.session.commit()

    def findgenre(self, genre):
        _genre = self.session.query(Genre).filter(sql.func.lower(Genre.genre) == genre).first()
        if not _genre:
            genre_id = 0
        else:
            genre_id = _genre.genre_id
        return genre_id

    def findbgenre(self, book_id, genre_id):
        try:
            book = self.session.query(Book).filter(Book.book_id == book_id).one()
            genre = self.session.query(Genre).filter(Genre.genre_id == genre_id).one()
        except orm.exc.NoResultFound:
            return False
        result = genre in book.genres
        return result

    def addgenre(self, genre):
        genre_id = self.findgenre(genre)
        if genre_id != 0:
            return genre_id
        _genre = Genre(genre, UNKNOWN_GENRE, genre)
        self.session.add(_genre)
        self.session.commit()
        return _genre.genre_id

    def addbgenre(self, book_id, genre_id):
        book = self.session.query(Book).filter(Book.book_id == book_id).one()
        genre = self.session.query(Genre).filter(Genre.genre_id == genre_id).one()
        book.genres.append(genre)
        self.session.commit()

    def findcat(self, catalog):
        (head, tail) = os.path.split(catalog)
        _catalog = self.session.query(Catalog). \
            filter(Catalog.cat_name == tail, Catalog.path == catalog). \
            order_by(Catalog.cat_id).first()
        if not _catalog:
            cat_id = 0
        else:
            cat_id = _catalog.cat_id
        return cat_id

    def addcattree(self, catalog, archive=0):
        cat_id = self.findcat(catalog)
        if cat_id != 0:
            return cat_id
        if catalog == '':
            return 0
        (head, tail) = os.path.split(catalog)
        if tail == '':
            parent_id = 0
        else:
            parent_id = self.addcattree(head)
        _catalog = Catalog(parent_id, tail, catalog, archive)
        self.session.add(_catalog)
        self.session.commit()
        return _catalog.cat_id

    def getcatinparent(self, parent_id, limit=0, page=0):
        query = self.session.query(Catalog.cat_id, Catalog.cat_name). \
                filter(Catalog.parent_id == parent_id). \
                order_by(Catalog.cat_name)
        if limit == 0:
            rows = query.all()
        else:
            offset = limit * page
            rows = query[offset:limit]
        return rows

    def getbooksincat(self, cat_id, limit=0, page=0):
        query = self.session.query(Book.book_id, Book.filename, Book.path, Book.registerdate). \
                filter(Book.cat_id == cat_id). \
                order_by(Book.filename)
        if limit == 0:
            rows = query.all()
        else:
            offset = limit * page
            rows = query[offset:limit]
        return rows

    def getitemsincat(self, cat_id, limit=0, page=0):
        query1 = self.session.query(1, Catalog.cat_id, Catalog.cat_name, Catalog.path, sql.func.now(),
                                    Catalog.cat_name.label('title')).filter(Catalog.parent_id == cat_id)
        query2 = self.session.query(2, Book.book_id, Book.filename, Book.path, Book.registerdate,
                                    Book.title).filter(Book.cat_id == cat_id)
        if limit == 0:
            rows = query1.union(query2).order_by(1, 6).all()
            self.next_page = False
        else:
            found_rows = query1.union(query2).count()
            offset = limit * page
            rows = query1.union(query2).order_by(1, 6)[offset:limit]
            self.next_page = (found_rows > (offset + limit))
        return rows

    def getbook(self, book_id):
        row = self.session.query(Book.filename, Book.path, Book.registerdate, Book.format, Book.title, Book.cat_type,
                                 Book.cover, Book.cover_type, Book.filesize). \
                                 filter(Book.book_id == book_id).one()
        return row

    def getauthors(self, book_id):
        book = self.session.query(Book).filter(Book.book_id == book_id).one()
        rows = [(author.first_name, author.last_name) for author in book.authors]
        return rows

    def getgenres(self, book_id):
        book = self.session.query(Book).filter(Book.book_id == book_id).one()
        rows = [(genre.section, genre.subsection) for genre in book.genres]
        return rows

    # def getauthor_2letters(self, letters):
    #     lc = len(letters) + 1
    #     sql = "select UPPER(substring(trim(CONCAT(last_name,' ',first_name)),1," + str(
    #         lc) + ")) as letters, count(*) as cnt from " + TBL_AUTHORS + " where UPPER(substring(trim(CONCAT(last_name,' ',first_name)),1," + str(
    #         lc - 1) + "))='" + letters + "' group by 1 order by 1"
    #     cursor = self.cnx.cursor()
    #     cursor.execute(sql)
    #     rows = cursor.fetchall()
    #     cursor.close
    #     return rows
    #
    # def gettitle_2letters(self, letters, doublicates=True):
    #     if doublicates:
    #         dstr = ''
    #     else:
    #         dstr = ' and doublicat=0 '
    #     lc = len(letters) + 1
    #     sql = "select UPPER(substring(trim(title),1," + str(
    #         lc) + ")) as letteris, count(*) as cnt from " + TBL_BOOKS + " where UPPER(substring(trim(title),1," + str(
    #         lc - 1) + "))='" + letters + "' " + dstr + " group by 1 order by 1"
    #     cursor = self.cnx.cursor()
    #     cursor.execute(sql)
    #     rows = cursor.fetchall()
    #     cursor.close
    #     return rows

    def getbooksfortitle(self, letters, limit=0, page=0, doublicates=True):
        query = self.session.query(Book.book_id, Book.filename, Book.path, Book.registerdate, Book.title, Book.cover,
                                   Book.cover_type).filter(Book.title.like(letters + '%'))
        if not doublicates:
            query = query.filter(Book.doublicat == 0)
        if limit == 0:
            rows = query.all()
            self.next_page = False
        else:
            found_rows = query.count()
            offset = limit * page
            rows = query[offset:limit]
            self.next_page = (found_rows > (offset + limit))
        return rows

    # def getauthorsbyl(self, letters, limit=0, page=0, doublicates=True):
    #     if limit == 0:
    #         limitstr = ""
    #     else:
    #         limitstr = "limit " + str(limit * page) + "," + str(limit)
    #     if doublicates:
    #         dstr = ''
    #     else:
    #         dstr = ' and c.doublicat=0 '
    #     sql = "select SQL_CALC_FOUND_ROWS a.author_id, a.first_name, a.last_name, count(*) as cnt from " + TBL_AUTHORS + " a, " + TBL_BAUTHORS + " b, " + TBL_BOOKS + " c where a.author_id=b.author_id and b.book_id=c.book_id and UPPER(a.last_name) like '" + letters + "%' " + dstr + " group by 1,2,3 order by 3,2 " + limitstr
    #     cursor = self.cnx.cursor()
    #     cursor.execute(sql)
    #     rows = cursor.fetchall()
    #
    #     cursor.execute("SELECT FOUND_ROWS()")
    #     found_rows = cursor.fetchone()
    #     if found_rows[0] > limit * page + limit:
    #         self.next_page = True
    #     else:
    #         self.next_page = False
    #
    #     cursor.close
    #     return rows
    #
    # def getbooksforautor(self, author_id, limit=0, page=0, doublicates=True):
    #     author = self.session.query(Author).filter(Author.author_id == author_id).one()
    #
    #     if limit == 0:
    #         limitstr = ""
    #     else:
    #         limitstr = "limit " + str(limit * page) + "," + str(limit)
    #     if doublicates:
    #         dstr = ''
    #     else:
    #         dstr = ' and a.doublicat=0 '
    #     sql = "select SQL_CALC_FOUND_ROWS a.book_id,a.filename,a.path,a.registerdate,a.title,a.cover,a.cover_type from " + TBL_BOOKS + " a, " + TBL_BAUTHORS + " b where a.book_id=b.book_id and b.author_id=" + str(
    #         author_id) + dstr + " order by a.title " + limitstr
    #     cursor = self.cnx.cursor()
    #     cursor.execute(sql)
    #     rows = cursor.fetchall()
    #
    #     cursor.execute("SELECT FOUND_ROWS()")
    #     found_rows = cursor.fetchone()
    #     if found_rows[0] > limit * page + limit:
    #         self.next_page = True
    #     else:
    #         self.next_page = False
    #
    #     cursor.close
    #     return rows

    def getlastbooks(self, limit=0):
        query = self.session.query(Book.book_id, Book.filename, Book.path, Book.registerdate, Book.title). \
            order_by(Book.registerdate.desc())
        if limit == 0:
            rows = query.all()
        else:
            rows = query[:limit]
        return rows

    # def getgenres_sections(self):
    #     rows = self.session.query()
    #     sql = "select min(a.genre_id), a.section, count(*) as cnt from " + TBL_GENRES + " a, " +\
    #           TBL_BGENRES + " b where a.genre_id=b.genre_id group by a.section order by a.section"
    #     cursor = self.cnx.cursor()
    #     cursor.execute(sql)
    #     rows = cursor.fetchall()
    #     cursor.close
    #     return rows
    #
    # def getgenres_subsections(self, section_id):
    #     sql = "select a.genre_id, a.subsection, count(*) as cnt from " + TBL_GENRES + " a, " + \
    #           TBL_BGENRES + " b where a.genre_id=b.genre_id and section in (select section from " + TBL_GENRES + " where genre_id=" + str(
    #         section_id) + ") group by a.subsection order by a.subsection"
    #     cursor = self.cnx.cursor()
    #     cursor.execute(sql)
    #     rows = cursor.fetchall()
    #     cursor.close
    #     return rows
    #
    # def getbooksforgenre(self, genre_id, limit=0, page=0, doublicates=True):
    #     if limit == 0:
    #         limitstr = ""
    #     else:
    #         limitstr = "limit " + str(limit * page) + "," + str(limit)
    #     if doublicates:
    #         dstr = ''
    #     else:
    #         dstr = ' and a.doublicat=0 '
    #     sql = "select SQL_CALC_FOUND_ROWS a.book_id,a.filename,a.path,a.registerdate,a.title,a.cover,a.cover_type from " + TBL_BOOKS + " a, " + TBL_BGENRES + " b where a.book_id=b.book_id and b.genre_id=" + str(
    #         genre_id) + dstr + " order by a.lang desc, a.title " + limitstr
    #     cursor = self.cnx.cursor()
    #     cursor.execute(sql)
    #     rows = cursor.fetchall()
    #
    #     cursor.execute("SELECT FOUND_ROWS()")
    #     found_rows = cursor.fetchone()
    #     if found_rows[0] > limit * page + limit:
    #         self.next_page = True
    #     else:
    #         self.next_page = False
    #
    #     cursor.close
    #     return rows

    def getdbinfo(self, doublicates=True):
        query = self.session.query(sql.func.count(Book.book_id))
        if not doublicates:
            query = query.filter(Book.doublicat == 0)
        query = query.union_all(self.session.query(sql.func.count(Author.author_id)),
                            self.session.query(sql.func.count(Catalog.cat_id)))
        rows = query.all()
        return rows

    def zipisscanned(self, zipname):
        _catalog = self.session.query(Catalog).filter(Catalog.path == zipname).first()
        if not _catalog:
            cat_id = 0
        else:
            cat_id = _catalog.cat_id
        return cat_id

    def __del__(self):
        self.closeDB()


    def init_db(self):
        """
        Инициализация базы данных

        """
        if not self.isopen:
            self.openDB()
        Base.metadata.create_all(self.engine)
        self.addauthor('', UNKNOWN_AUTHOR)

        self.session.add(Genre("sf_history", "Альтернативная история", "Фантастика"))
        self.session.add(Genre("sf_action", "Боевая фантастика", "Фантастика"))
        self.session.add(Genre("sf_epic", "Эпическая фантастика", "Фантастика"))
        self.session.add(Genre("sf_heroic", "Героическая фантастика", "Фантастика"))
        self.session.add(Genre("sf_detective", "Детективная фантастика", "Фантастика"))
        self.session.add(Genre("sf_cyberpunk", "Киберпанк", "Фантастика"))
        self.session.add(Genre("sf_space", "Космическая фантастика", "Фантастика"))
        self.session.add(Genre("sf_social", "Социально психологическая фантастика", "Фантастика"))
        self.session.add(Genre("sf_horror", "Ужасы и Мистика", "Фантастика"))
        self.session.add(Genre("sf_humor", "Юмористическая фантастика", "Фантастика"))
        self.session.add(Genre("sf_fantasy", "Фэнтези", "Фантастика"))
        self.session.add(Genre("sf", "Научная Фантастика", "Фантастика"))
        self.session.add(Genre("det_classic", "Классический детектив", "Детективы и Триллеры"))
        self.session.add(Genre("det_police", "Полицейский детектив", "Детективы и Триллеры"))
        self.session.add(Genre("det_action", "Боевик", "Детективы и Триллеры"))
        self.session.add(Genre("det_irony", "Иронический детектив", "Детективы и Триллеры"))
        self.session.add(Genre("det_history", "Исторический детектив", "Детективы и Триллеры"))
        self.session.add(Genre("det_espionage", "Шпионский детектив", "Детективы и Триллеры"))
        self.session.add(Genre("det_crime", "Криминальный детектив", "Детективы и Триллеры"))
        self.session.add(Genre("det_political", "Политический детектив", "Детективы и Триллеры"))
        self.session.add(Genre("det_maniac", "Маньяки", "Детективы и Триллеры"))
        self.session.add(Genre("det_hard", "Крутой детектив", "Детективы и Триллеры"))
        self.session.add(Genre("thriller", "Триллер", "Детективы и Триллеры"))
        self.session.add(Genre("detective", "Детектив (не относящийся в прочие категории).", "Детективы и Триллеры"))
        self.session.add(Genre("prose_classic", "Классическая проза", "Проза"))
        self.session.add(Genre("prose_history", "Историческая проза", "Проза"))
        self.session.add(Genre("prose_contemporary", "Современная проза", "Проза"))
        self.session.add(Genre("prose_counter", "Контркультура", "Проза"))
        self.session.add(Genre("prose_rus_classic", "Русская классическая проза", "Проза"))
        self.session.add(Genre("prose_su_classics", "Советская классическая проза", "Проза"))
        self.session.add(Genre("love_contemporary", "Современные любовные романы", "Любовные романы"))
        self.session.add(Genre("love_history", "Исторические любовные романы", "Любовные романы"))
        self.session.add(Genre("love_detective", "Остросюжетные любовные романы", "Любовные романы"))
        self.session.add(Genre("love_short", "Короткие любовные романы", "Любовные романы"))
        self.session.add(Genre("love_erotica", "Эротика", "Любовные романы"))
        self.session.add(Genre("adv_western", "Вестерн", "Приключения"))
        self.session.add(Genre("adv_history", "Исторические приключения", "Приключения"))
        self.session.add(Genre("adv_indian", "Приключения про индейцев", "Приключения"))
        self.session.add(Genre("adv_maritime", "Морские приключения", "Приключения"))
        self.session.add(Genre("adv_geo", "Путешествия и география", "Приключения"))
        self.session.add(Genre("adv_animal", "Природа и животные", "Приключения"))
        self.session.add(Genre("adventure", "Прочие приключения", "Приключения"))
        self.session.add(Genre("child_tale", "Сказка", "Детская литература"))
        self.session.add(Genre("child_verse", "Детские стихи", "Детская литература"))
        self.session.add(Genre("child_prose", "Детскиая проза", "Детская литература"))
        self.session.add(Genre("child_sf", "Детская фантастика", "Детская литература"))
        self.session.add(Genre("child_det", "Детские остросюжетные", "Детская литература"))
        self.session.add(Genre("child_adv", "Детские приключения", "Детская литература"))
        self.session.add(Genre("child_education", "Детская образовательная литература", "Детская литература"))
        self.session.add(Genre("children", "Прочая детская литература", "Детская литература"))
        self.session.add(Genre("poetry", "Поэзия", "Поэзия, Драматургия"))
        self.session.add(Genre("dramaturgy", "Драматургия", "Поэзия, Драматургия"))
        self.session.add(Genre("antique_ant", "Античная литература", "Старинное"))
        self.session.add(Genre("antique_european", "Европейская старинная литература", "Старинное"))
        self.session.add(Genre("antique_russian", "Древнерусская литература", "Старинное"))
        self.session.add(Genre("antique_east", "Древневосточная литература", "Старинное"))
        self.session.add(Genre("antique_myths", "Мифы. Легенды. Эпос", "Старинное"))
        self.session.add(Genre("antique", "Прочая старинная литература", "Старинное"))
        self.session.add(Genre("sci_history", "История", "Наука, Образование"))
        self.session.add(Genre("sci_psychology", "Психология", "Наука, Образование"))
        self.session.add(Genre("sci_culture", "Культурология", "Наука, Образование"))
        self.session.add(Genre("sci_religion", "Религиоведение", "Наука, Образование"))
        self.session.add(Genre("sci_philosophy", "Философия", "Наука, Образование"))
        self.session.add(Genre("sci_politics", "Политика", "Наука, Образование"))
        self.session.add(Genre("sci_business", "Деловая литература", "Наука, Образование"))
        self.session.add(Genre("sci_juris", "Юриспруденция", "Наука, Образование"))
        self.session.add(Genre("sci_linguistic", "Языкознание", "Наука, Образование"))
        self.session.add(Genre("sci_medicine", "Медицина", "Наука, Образование"))
        self.session.add(Genre("sci_phys", "Физика", "Наука, Образование"))
        self.session.add(Genre("sci_math", "Математика", "Наука, Образование"))
        self.session.add(Genre("sci_chem", "Химия", "Наука, Образование"))
        self.session.add(Genre("sci_biology", "Биология", "Наука, Образование"))
        self.session.add(Genre("sci_tech", "Технические науки", "Наука, Образование"))
        self.session.add(Genre("science", "Прочая научная литература", "Наука, Образование"))
        self.session.add(Genre("comp_www", "Интернет", "Компьютеры и Интернет"))
        self.session.add(Genre("comp_programming", "Программирование", "Компьютеры и Интернет"))
        self.session.add(Genre("comp_hard", "Компьютерное железо", "Компьютеры и Интернет"))
        self.session.add(Genre("comp_soft", "Программы", "Компьютеры и Интернет"))
        self.session.add(Genre("comp_db", "Базы данных", "Компьютеры и Интернет"))
        self.session.add(Genre("comp_osnet", "ОС и Сети", "Компьютеры и Интернет"))
        self.session.add(Genre("computers", "Прочая околокомпьтерная литература", "Компьютеры и Интернет"))
        self.session.add(Genre("ref_encyc", "Энциклопедии", "Справочная литература"))
        self.session.add(Genre("ref_dict", "Словари", "Справочная литература"))
        self.session.add(Genre("ref_ref", "Справочники", "Справочная литература"))
        self.session.add(Genre("ref_guide", "Руководства", "Справочная литература"))
        self.session.add(Genre("reference", "Прочая справочная литература", "Справочная литература"))
        self.session.add(Genre("nonf_biography", "Биографии и Мемуары", "Документальная литература"))
        self.session.add(Genre("nonf_publicism", "Публицистика", "Документальная литература"))
        self.session.add(Genre("nonf_criticism", "Критика", "Документальная литература"))
        self.session.add(Genre("design", "Искусство и Дизайн", "Документальная литература"))
        self.session.add(Genre("nonfiction", "Прочая документальная литература", "Документальная литература"))
        self.session.add(Genre("religion_rel", "Религия", "Религия и духовность"))
        self.session.add(Genre("religion_esoterics", "Эзотерика", "Религия и духовность"))
        self.session.add(Genre("religion_self", "Самосовершенствование", "Религия и духовность"))
        self.session.add(Genre("religion", "Прочая религионая литература", "Религия и духовность"))
        self.session.add(Genre("humor_anecdote", "Анекдоты", "Юмор"))
        self.session.add(Genre("humor_prose", "Юмористическая проза", "Юмор"))
        self.session.add(Genre("humor_verse", "Юмористические стихи", "Юмор"))
        self.session.add(Genre("humor", "Прочий юмор", "Юмор"))
        self.session.add(Genre("home_cooking", "Кулинария", "Дом и семья"))
        self.session.add(Genre("home_pets", "Домашние животные", "Дом и семья"))
        self.session.add(Genre('home_crafts', "Хобби и ремесла", "Дом и семья"))
        self.session.add(Genre("home_entertain", "Развлечения", "Дом и семья"))
        self.session.add(Genre("home_health", "Здоровье", "Дом и семья"))
        self.session.add(Genre("home_garden", "Сад и огород", "Дом и семья"))
        self.session.add(Genre("home_diy", "Сделай сам", "Дом и семья"))
        self.session.add(Genre("home_sport", "Спорт", "Дом и семья"))
        self.session.add(Genre("home_sex", "Эротика, Секс", "Дом и семья"))
        self.session.add(Genre("home", "Прочее домоводство", "Дом и семья"))
        self.session.commit()


if __name__ == '__main__':
    import unittest
    PATH = 'С:/Путь книги'
    FIRST = 'Первое Имя'
    LAST = 'Второе Имя'
    PATH_BOOK = os.path.join(PATH, FIRST, LAST)
    FILENAME = 'Book.fb2'
    TILE_BOOK = 'Имя Книжки'
    FORMAT = 'fb2'
    SIZE_BOOK = 1024

    class Test(unittest.TestCase):

        def setUp(self):
            self.db = opdsDatabase('sqlite:///:memory:')
            self.db.init_db()

        def test_findbook(self):
            self.assertEqual(self.db.findbook(FILENAME, PATH_BOOK), 0)
            self.db.session.add(Book(FILENAME, PATH_BOOK, 0, 0, '', '', '', 0, 0))
            self.assertEqual(self.db.findbook(FILENAME, PATH_BOOK), 1)
            self.db.session.add(Book(FILENAME, PATH_BOOK, 0, 0, '', '', '', 0, 0))
            self.assertEqual(self.db.findbook(FILENAME, PATH_BOOK), 1)

        def test_finddouble(self):
            self.assertEqual(self.db.finddouble(TILE_BOOK,FORMAT,SIZE_BOOK), 0)
            self.db.session.add(Book(FILENAME, PATH_BOOK, 0, SIZE_BOOK, FORMAT, TILE_BOOK, '', 0, 1))
            self.assertEqual(self.db.finddouble(TILE_BOOK,FORMAT,SIZE_BOOK), 0)
            self.db.session.add(Book(FILENAME, PATH_BOOK, 0, SIZE_BOOK, FORMAT, TILE_BOOK, '', 0, 0))
            self.assertEqual(self.db.finddouble(TILE_BOOK,FORMAT,SIZE_BOOK), 2)

        def test_addbook(self):
            self.assertEqual(self.db.addbook(FILENAME, PATH_BOOK, 0, '.'+FORMAT, SIZE_BOOK, TILE_BOOK, '', 0, 0), 1)
            self.assertEqual(self.db.addbook(FILENAME, PATH_BOOK, 0, '.'+FORMAT, SIZE_BOOK, TILE_BOOK, '', 0, 0), 1)
            self.assertEqual(self.db.addbook(FILENAME, PATH_BOOK+'/', 0, '.'+FORMAT, SIZE_BOOK, TILE_BOOK, '', 0, 0), 2)

        def test_addcover(self):
            book_id = self.db.addbook(FILENAME, PATH_BOOK, 0, '.'+FORMAT, SIZE_BOOK, TILE_BOOK, '', 0, 0)
            self.db.addcover(book_id, FILENAME, FORMAT)
            book = self.db.session.query(Book).filter(Book.book_id == book_id).one()
            self.assertEqual(book.cover, FILENAME)
            self.assertEqual(book.cover_type, FORMAT)

        def test_findauthor(self):
            self.assertEqual(self.db.findauthor('Какойто', 'Fdnjh'), 0)
            self.assertEqual(self.db.findauthor('', UNKNOWN_AUTHOR), 1)

        def test_findbauthor(self):
            book_id = self.db.addbook(FILENAME, PATH_BOOK, 0, '.'+FORMAT, SIZE_BOOK, TILE_BOOK, '', 0, 0)
            author_id = self.db.addauthor(FIRST, LAST)
            self.assertNotEqual(book_id, 0)
            self.assertNotEqual(author_id, 0)
            self.db.addbauthor(book_id, author_id)
            self.db.addbauthor(book_id, author_id)
            self.assertFalse(self.db.findbauthor(book_id, 1))
            self.db.addbauthor(book_id, 1)
            self.assertTrue(self.db.findbauthor(book_id, author_id))
            self.assertTrue(self.db.findbauthor(book_id, 1))

        def test_addauthor(self):
            self.db.addauthor(FIRST, LAST)
            self.assertEqual(self.db.findauthor(FIRST, LAST), 2)

        def test_addbauthor(self):
            book_id = self.db.addbook(FILENAME, PATH_BOOK, 0, '.'+FORMAT, SIZE_BOOK, TILE_BOOK, '', 0, 0)
            author_id = self.db.addauthor(FIRST, LAST)
            self.assertNotEqual(book_id, 0)
            self.assertNotEqual(author_id, 0)
            self.db.addbauthor(book_id, author_id)
            self.db.addbauthor(book_id, author_id)
            self.db.addbauthor(book_id, 1)
            self.assertEqual(self.db.session.query(book_authors).count(), 2)

        def test_findgenre(self):
            self.assertEqual(self.db.findgenre('unknown'), 0)
            self.assertEqual(self.db.findgenre('sf_humor'), 10)

        def test_findbgenre(self):
            book_id = self.db.addbook(FILENAME, PATH_BOOK, 0, '.'+FORMAT, SIZE_BOOK, TILE_BOOK, '', 0, 0)
            self.db.addbgenre(book_id, 10)
            self.db.addbgenre(book_id, 10)
            self.assertFalse(self.db.findbgenre(book_id, 1))
            self.db.addbgenre(book_id, 1)
            self.assertTrue(self.db.findbgenre(book_id, 10))
            self.assertTrue(self.db.findbgenre(book_id, 1))

        def test_addgenre(self):
            self.assertEqual(self.db.addgenre('sf_humor'), 10)
            genre_id = self.db.addgenre('unknown')
            self.assertNotEqual(genre_id, 0)
            genre = self.db.session.query(Genre).filter(Genre.genre_id == genre_id).one()
            self.assertEqual(genre.genre_id, genre_id)
            self.assertEqual(genre.genre, 'unknown')
            self.assertEqual(genre.subsection, UNKNOWN_GENRE)

        def test_addbgenre(self):
            book_id = self.db.addbook(FILENAME, PATH_BOOK, 0, '.'+FORMAT, SIZE_BOOK, TILE_BOOK, '', 0, 0)
            self.assertNotEqual(book_id, 0)
            self.db.addbgenre(book_id, 10)
            self.db.addbgenre(book_id, 10)
            self.db.addbgenre(book_id, 1)
            self.assertEqual(self.db.session.query(book_genre).count(), 2)

        def test_findcat(self):
            self.assertEqual(self.db.findcat(PATH_BOOK), 0)
            cat_id = self.db.addcattree(PATH_BOOK)
            self.assertEqual(self.db.findcat(PATH_BOOK), cat_id)

        def test_addcattree(self):
            cat_id = self.db.addcattree(PATH_BOOK)
            self.assertEqual(self.db.findcat(PATH_BOOK), cat_id)
            self.assertNotEqual(self.db.findcat(PATH), 0)
            self.assertNotEqual(self.db.findcat(os.path.join(PATH, FIRST)), 0)

        def test_getcatinparent(self):
            self.assertEqual(len(self.db.getcatinparent(100)), 0)
            cat_id = self.db.addcattree(PATH_BOOK)
            self.assertNotEqual(cat_id, 0)
            self.assertEqual(len(self.db.getcatinparent(cat_id)), 0)
            self.assertEqual(len(self.db.getcatinparent(cat_id, 10)), 0)
            cat_id = self.db.findcat(PATH)
            self.assertNotEqual(cat_id, 0)
            self.assertEqual(len(self.db.getcatinparent(cat_id)), 1)
            self.assertEqual(len(self.db.getcatinparent(cat_id, 1)), 1)
            cat_id = self.db.findcat(os.path.join(PATH, FIRST))
            self.assertNotEqual(cat_id, 0)
            self.assertEqual(len(self.db.getcatinparent(cat_id)), 1)
            self.assertEqual(len(self.db.getcatinparent(cat_id, 1, 1)), 0)

        def test_getbooksincat(self):
            cat_id = self.db.addcattree(PATH_BOOK)
            self.assertEqual(len(self.db.getbooksincat(cat_id)), 0)
            book_id = self.db.addbook(FILENAME, PATH_BOOK, cat_id, '.'+FORMAT, SIZE_BOOK, TILE_BOOK, '', 0, 0)
            self.db.addbook(FILENAME, PATH_BOOK, cat_id, '.'+FORMAT, SIZE_BOOK, TILE_BOOK, '', 0, 0)
            self.assertEqual(len(self.db.getbooksincat(cat_id)), 1)
            self.assertEqual(self.db.getbooksincat(cat_id)[0][0], book_id)
            self.db.addbook(FILENAME, PATH_BOOK+'/', cat_id, '.'+FORMAT, SIZE_BOOK, TILE_BOOK, '', 0, 0)
            self.assertEqual(len(self.db.getbooksincat(cat_id)), 2)
            self.assertEqual(len(self.db.getbooksincat(cat_id, 1)), 1)
            self.assertEqual(len(self.db.getbooksincat(cat_id, 1, 1)), 1)
            self.assertEqual(len(self.db.getbooksincat(cat_id, 2, 0)), 2)

        def test_getitemsincat(self):
            pass

        def test_getbook(self):
            pass

        def test_getauthors(self):
            pass

        def test_getgenres(self):
            pass

        def test_getauthor_2letters(self):
            pass

        def test_gettitle_2letters(self):
            pass

        def getbooksfortitle(self):
            pass

        def test_getauthorsbyl(self):
            pass

        def test_getbooksforautor(self):
            pass

        def test_getlastbooks(self):
            pass

        def test_getgenres_sections(self):
            pass

        def test_getgenres_subsections(self):
            pass

        def test_getbooksforgenre(self):
            pass

        def test_getdbinfo(self):
            self.assertEqual(self.db.getdbinfo(), [(0,), (1,), (0,)])

        def test_zipisscanned(self):
            pass

    unittest.main()
