# -*- coding: utf-8 -*-
__author__ = 'vseklecov'

##########################################################################
# типы каталогов (cat_type)
#
CAT_NORMAL=0
CAT_ZIP=1
CAT_GZ=2

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
    search_title = sql.Column(sql.String(256), index=True)

    authors = orm.relationship('Author', secondary=book_authors, backref='books')
    genres = orm.relationship('Genre', secondary=book_genre, backref='books')

    def __init__(self, file_name='fn', path='/', cat_id=0, format_book='fb2', title='title', lang='ru',
                 size=0, archive=0, doublicat=0):
        self.filename = file_name
        self.path = path
        self.cat_id = cat_id
        self.filesize = size
        self.format = format_book
        self.title = title
        self.lang = lang
        self.cat_type = archive
        self.doublicat = doublicat
        self.search_title = self.title.lower()

    def cat_normal(self):
        return self.cat_type == CAT_NORMAL

    def cat_zip(self):
        return self.cat_type == CAT_ZIP

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

    def __init__(self, parent_id=0, cat_name='dir', path='/', cat_type=0):
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

    def __init__(self, last_name='name', first_name=''):
        self.last_name = last_name
        self.first_name = first_name
        self.search_name = last_name.lower()+' '+first_name.lower()

    def __repr__(self):
        return "<Author('%s %s')>" % (self.last_name, self.first_name)

    def __str__(self):
        return '{0:s} {1:s}'.format(self.last_name, self.first_name)

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
        self.is_open = False
        self.next_page = False

    def open_db(self):
        if not self.is_open:
            try:
                self.engine = sql.create_engine(self.db_name)
                Session = orm.sessionmaker(bind=self.engine)
                self.session = Session()
            except:
                self.err = ''
                self.errcode = 1
            else:
                self.is_open = True
        else:
            self.errcode = 1
            self.err = 'Error open database. Database already open.'

    def close_db(self):
        if self.is_open:
            self.session.close()
            self.is_open = False
        else:
            self.errcode = 5
            self.err = 'Attempt to close not opened database.'

    def print_db_err(self):
        if self.errcode == 0:
            print("No database error found.")
        else:
            print("Error code =", self.errcode, ".Error message:", self.err)

    def clear_db_err(self):
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
        format_book = exten[1:].lower()
        if doublicates != 0:
            doublicat = self.finddouble(title, format_book, size)
        else:
            doublicat = 0
        book = Book(name, path, cat_id, format_book, title, lang, size, archive, doublicat)
        self.session.add(book)
        self.session.commit()
        return book.book_id

    def addcover(self, book_id, fn, cover_type):
        book = self.session.query(Book).get(book_id)
        if not book:
            return
        book.cover = fn
        book.cover_type = cover_type
        self.session.commit()

    def findauthor(self, first_name, last_name):
        search_name = last_name.lower()+' '+first_name.lower()
        author = self.session.query(Author).filter(Author.search_name == search_name).first()
        return author

    def findbauthor(self, book_id, author_id):
        book = self.session.query(Book).get(book_id)
        author = self.session.query(Author).get(author_id)
        if not book or not author:
            return False
        result = author in book.authors
        return result

    def addauthor(self, first_name, last_name):
        author = self.findauthor(first_name, last_name)
        if author:
            return author
        author = Author(last_name, first_name)
        self.session.add(author)
        self.session.commit()
        return author

    def addbauthor(self, book_id, author_id):
        book = self.session.query(Book).get(book_id)
        author = self.session.query(Author).get(author_id)
        if not book or not author:
            return
        book.authors.append(author)
        self.session.commit()

    def findgenre(self, genre):
        return self.session.query(Genre).filter(sql.func.lower(Genre.genre) == genre).first()

    def findbgenre(self, book_id, genre_id):
        book = self.session.query(Book).get(book_id)
        genre = self.session.query(Genre).get(genre_id)
        if not book or not genre:
            return False
        result = genre in book.genres
        return result

    def addgenre(self, genre):
        _genre = self.findgenre(genre)
        if not _genre:
            _genre = Genre(_genre, UNKNOWN_GENRE, _genre)
            self.session.add(_genre)
            self.session.commit()
        return _genre

    def addbgenre(self, book_id, genre_id):
        book = self.session.query(Book).get(book_id)
        genre = self.session.query(Genre).get(genre_id)
        if not book or not genre:
            return
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
            rows = query[offset:(offset+limit)]
        return rows

    def getbooksincat(self, cat_id, limit=0, page=0):
        query = self.session.query(Book.book_id, Book.filename, Book.path, Book.registerdate). \
                filter(Book.cat_id == cat_id). \
                order_by(Book.filename)
        if limit == 0:
            rows = query.all()
        else:
            offset = limit * page
            rows = query[offset:(offset+limit)]
        return rows

    def getitemsincat(self, cat_id, limit=0, page=0):
        query1 = self.session.query(sql.sql.expression.literal_column('1').label('cat'), Catalog.cat_id, Catalog.cat_name, Catalog.path, sql.func.now(),
                                    Catalog.cat_name.label('title')).filter(Catalog.parent_id == cat_id)
        query2 = self.session.query(sql.sql.expression.literal_column('2'), Book.book_id, Book.filename, Book.path, Book.registerdate,
                                    Book.title).filter(Book.cat_id == cat_id)
        if limit == 0:
            rows = query1.union(query2).order_by('1', '6').all()
            self.next_page = False
        else:
            found_rows = query1.union(query2).count()
            offset = limit * page
            rows = query1.union(query2).order_by('1', '6')[offset:(offset+limit)]
            self.next_page = (found_rows > (offset+limit))
        return rows

    def getbook(self, book_id):
        return self.session.query(Book).get(book_id)

    def getauthors(self, book_id):
        book = self.session.query(Book).get(book_id)
        if not book:
            return tuple()
        rows = [(author.first_name, author.last_name) for author in book.authors]
        return rows

    def getgenres(self, book_id):
        book = self.session.query(Book).get(book_id)
        if not book:
            return tuple()
        rows = [(genre.section, genre.subsection) for genre in book.genres]
        return rows

    def getauthor_2letters(self, letters):
        lc = len(letters) + 1
        query = self.session.query(sql.func.substr(Author.search_name, 1, lc).label('letters'),
                                   sql.func.count('*').label('cnt')).\
            filter(Author.search_name.like(letters.lower()+'%')).group_by('1').order_by('1')
        return query.all()

    def gettitle_2letters(self, letters, doublicates=True):
        lc = len(letters) + 1
        query = self.session.query(sql.func.substr(Book.title, 1, lc).label('letters'),
                                   sql.func.count('*').label('cnt')).\
            filter(Book.search_title.like(letters.lower()+'%'))
        if not doublicates:
            query = query.filter(Book.doublicat == 0)
        query = query.group_by('1').order_by('1')
        return query.all()

    def getbooksfortitle(self, letters, limit=0, page=0, doublicates=True):
        query = self.session.query(Book).filter(Book.title.like(letters + '%'))
        if not doublicates:
            query = query.filter(Book.doublicat == 0)
        if limit == 0:
            books = query.all()
            self.next_page = False
        else:
            found_rows = query.count()
            offset = limit * page
            books = query[offset:(offset+limit)]
            self.next_page = (found_rows > (offset+limit))
        return books

    def getauthorsbyl(self, letters, limit=0, page=0, doublicates=True):
        query = self.session.query(Author.author_id, Author.first_name, Author.last_name,
                                   sql.func.count(book_authors)).filter(Author.author_id == book_authors.c.author_id,
                                                                        Author.search_name.like(letters.lower()+'%'))
        if not doublicates:
            query = query.filter(book_authors.c.book_id == Book.book_id, Book.doublicat == 0)
        query = query.group_by('1', '2', '3')
        query = query.order_by(Author.search_name)
        if limit == 0:
            rows = query.all()
        else:
            found_rows = query.count()
            offset = limit * page
            rows = query[offset:(offset+limit)]
            self.next_page = (found_rows > (offset+limit))
        return rows

    def getbooksforauthor(self, author_id, limit=0, page=0, doublicates=True):
        query = self.session.query(Book).filter(Book.book_id == book_authors.c.book_id,
                                                book_authors.c.author_id == author_id)
        if not doublicates:
            query = query.filter(Book.doublicat == 0)
        query = query.order_by(Book.title)
        if limit == 0:
            books = query.all()
            self.next_page = False
        else:
            found_rows = query.count()
            offset = limit * page
            books = query[offset:(offset+limit)]
            self.next_page = (found_rows > (offset+limit))
        return books

    def getlastbooks(self, limit=0):
        query = self.session.query(Book).order_by(Book.registerdate.desc())
        if limit == 0:
            books = query.all()
        else:
            books = query[:limit]
        return books

    def getgenres_sections(self):
        squery = self.session.query(book_genre.c.genre_id, sql.func.count(book_genre.c.book_id).label('book_count')).\
            group_by(book_genre.c.genre_id).subquery()
        rows = self.session.query(sql.func.min(Genre.genre_id), Genre.section, sql.func.sum(squery.c.book_count)).\
            join(squery, Genre.genre_id == squery.c.genre_id).group_by(Genre.section).order_by(Genre.section).all()
        return rows

    def getgenres_subsections(self, section_id):
        genre = self.session.query(Genre).get(section_id)
        if not genre:
            return tuple()
        query = self.session.query(Genre.genre_id, Genre.subsection, sql.func.count(book_genre)).\
            filter(Genre.genre_id == book_genre.c.genre_id, Genre.section == genre.section).\
            group_by(Genre.genre_id, Genre.subsection).order_by(Genre.subsection)
        rows = query.all()
        return rows

    def getbooksforgenre(self, genre_id, limit=0, page=0, doublicates=True):
        query = self.session.query(Book).filter(Book.book_id == book_genre.c.book_id,
                                                book_genre.c.genre_id == genre_id)
        if not doublicates:
            query = query.filter(Book.doublicat == 0)
        query = query.order_by(Book.lang, Book.title)
        if limit == 0:
            books = query.all()
            self.next_page = False
        else:
            found_rows = query.count()
            offset = limit * page
            books = query[offset:(offset+limit)]
            self.next_page = (found_rows > (offset+limit))
        return books

    def getdbinfo(self, doublicates=True):
        query = self.session.query(sql.func.count(Book.book_id))
        if not doublicates:
            query = query.filter(Book.doublicat == 0)
        query = query.union_all(self.session.query(sql.func.count(Author.author_id)),
                            self.session.query(sql.func.count(Catalog.cat_id)))
        rows = query.all()
        return rows[0][0], rows[1][0], rows[2][0]


    def zipisscanned(self, zipname):
        _catalog = self.session.query(Catalog).filter(Catalog.path == zipname).order_by(Catalog.cat_id).first()
        if not _catalog:
            cat_id = 0
        else:
            cat_id = _catalog.cat_id
        return cat_id

    def __del__(self):
        self.close_db()


    def init_db(self):
        """
        Инициализация базы данных

        """
        if not self.is_open:
            self.open_db()
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
    import time

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
            self.assertEqual(self.db.finddouble(TILE_BOOK, FORMAT, SIZE_BOOK), 0)
            self.db.addbook(FILENAME, PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, 'ru', SIZE_BOOK, 0, 0)
            self.assertEqual(self.db.finddouble(TILE_BOOK, FORMAT, SIZE_BOOK), 1)
            self.db.addbook(FILENAME, PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, 'ru', SIZE_BOOK, 0, 1)
            self.assertEqual(self.db.finddouble(TILE_BOOK, FORMAT, SIZE_BOOK), 1)

        def test_addbook(self):
            #name, path, cat_id, exten, title, lang, size=0, archive=0, doublicates=0
            book_id = self.db.addbook(FILENAME, PATH_BOOK, 1, '.'+FORMAT, TILE_BOOK, 'ru', SIZE_BOOK, 2, 0)
            self.assertEqual(book_id, 1)
            book = self.db.session.query(Book).get(book_id)
            self.assertEqual(book.filename, FILENAME)
            self.assertEqual(book.path, PATH_BOOK)
            self.assertEqual(book.cat_id, 1)
            self.assertEqual(book.format, FORMAT)
            self.assertEqual(book.title, TILE_BOOK)
            self.assertEqual(book.lang, 'ru')
            self.assertEqual(book.filesize, SIZE_BOOK)
            self.assertEqual(book.cat_type, 2)
            self.assertEqual(book.doublicat, 0)
            self.assertEqual(self.db.addbook(FILENAME, PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0), 1)
            self.assertEqual(self.db.addbook(FILENAME, PATH_BOOK+'/', 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0), 2)

        def test_addcover(self):
            book_id = self.db.addbook(FILENAME, PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            self.db.addcover(book_id, FILENAME, FORMAT)
            book = self.db.session.query(Book).filter(Book.book_id == book_id).one()
            self.assertEqual(book.cover, FILENAME)
            self.assertEqual(book.cover_type, FORMAT)

        def test_findauthor(self):
            self.assertEqual(self.db.findauthor('Какойто', 'Fdnjh'), None)
            self.assertNotEqual(self.db.findauthor('', UNKNOWN_AUTHOR), None)

        def test_findbauthor(self):
            book_id = self.db.addbook(FILENAME, PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            author_id = self.db.addauthor(FIRST, LAST).author_id
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
            self.assertNotEqual(self.db.findauthor(FIRST, LAST), None)

        def test_addbauthor(self):
            book_id = self.db.addbook(FILENAME, PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            author_id = self.db.addauthor(FIRST, LAST).author_id
            self.assertNotEqual(book_id, 0)
            self.assertNotEqual(author_id, 0)
            self.db.addbauthor(book_id, author_id)
            self.db.addbauthor(book_id, author_id)
            self.db.addbauthor(book_id, 1)
            self.assertEqual(self.db.session.query(book_authors).count(), 2)

        def test_findgenre(self):
            self.assertEqual(self.db.findgenre('unknown').genre_id, 0)
            self.assertEqual(self.db.findgenre('sf_humor').genre_id, 10)

        def test_findbgenre(self):
            book_id = self.db.addbook(FILENAME, PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
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
            book_id = self.db.addbook(FILENAME, PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
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
            book_id = self.db.addbook(FILENAME, PATH_BOOK, cat_id, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            self.db.addbook(FILENAME, PATH_BOOK, cat_id, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            self.assertEqual(len(self.db.getbooksincat(cat_id)), 1)
            self.assertEqual(self.db.getbooksincat(cat_id)[0][0], book_id)
            self.db.addbook(FILENAME, PATH_BOOK+'/', cat_id, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            self.assertEqual(len(self.db.getbooksincat(cat_id)), 2)
            self.assertEqual(len(self.db.getbooksincat(cat_id, 1)), 1)
            self.assertEqual(len(self.db.getbooksincat(cat_id, 1, 1)), 1)
            self.assertEqual(len(self.db.getbooksincat(cat_id, 2, 0)), 2)

        def test_getitemsincat(self):
            self.db.addcattree(PATH_BOOK)
            cat_id = self.db.findcat(os.path.join(PATH, FIRST))
            self.assertEqual(len(self.db.getitemsincat(cat_id)), 1)
            self.db.addbook(FILENAME, PATH_BOOK, cat_id, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            self.assertEqual(len(self.db.getitemsincat(cat_id)), 2)
            self.db.addbook(FILENAME, os.path.join(PATH, FIRST), cat_id, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            self.assertEqual(len(self.db.getitemsincat(cat_id)), 3)
            self.db.addbook(FILENAME, os.path.join(PATH, FIRST), cat_id, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            self.assertEqual(len(self.db.getitemsincat(cat_id)), 3)
            self.assertEqual(len(self.db.getitemsincat(cat_id, 1)), 1)
            self.assertEqual(len(self.db.getitemsincat(cat_id, 1, 1)), 1)
            self.assertEqual(len(self.db.getitemsincat(cat_id, 2, 0)), 2)

        def test_getbook(self):
            self.assertEqual(self.db.getbook(0), None)
            book_id = self.db.addbook(FILENAME, PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            self.assertNotEqual(self.db.getbook(book_id), None)
            self.assertEqual(self.db.getbook(book_id).filename, FILENAME)

        def test_getauthors(self):
            book_id = self.db.addbook(FILENAME+'1', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, 'ru', SIZE_BOOK, 0, 0)
            author_id = self.db.addauthor(FIRST, LAST).author_id
            self.db.addbauthor(book_id, author_id)
            self.db.addbauthor(book_id, 1)
            self.assertEqual(len(self.db.getauthors(book_id)), 2)

        def test_getgenres(self):
            book_id = self.db.addbook(FILENAME+'1', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, 'ru', SIZE_BOOK, 0, 0)
            genre = self.db.findgenre('sf')
            self.db.addbgenre(book_id, genre.genre_id)
            self.assertEqual(len(self.db.getgenres(book_id)), 1)

        def test_getauthor_2letters(self):
            self.assertEqual(len(self.db.getauthor_2letters(LAST[:2])), 0)
            self.db.addauthor(FIRST, LAST)
            self.db.addauthor(FIRST, LAST+'1')
            rows = self.db.getauthor_2letters(LAST[:2])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][1], 2)

        def test_gettitle_2letters(self):
            self.assertEqual(len(self.db.gettitle_2letters(TILE_BOOK[:2])), 0)
            self.db.addbook(FILENAME+'1', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, 'ru', SIZE_BOOK, 0, 0)
            self.db.addbook(FILENAME+'2', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK+'1', 'ru', SIZE_BOOK, 0, 0)
            self.db.addbook(FILENAME+'3', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK+'2', 'ru', SIZE_BOOK, 0, 0)
            rows = self.db.gettitle_2letters(TILE_BOOK[:2])
            self.assertEqual(rows[0][0], TILE_BOOK[:3])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][1], 3)

        def test_getbooksfortitle(self):
            #name, path, cat_id, exten, title, lang, size=0, archive=0, doublicates=0
            book_id1 = self.db.addbook(FILENAME+'1', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, 'ru', SIZE_BOOK, 0, 0)
            book_id2 = self.db.addbook(FILENAME+'2', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK+'1', 'ru', SIZE_BOOK, 0, 0)
            book_id3 = self.db.addbook(FILENAME+'3', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK+'2', 'ru', SIZE_BOOK, 0, 0)
            self.assertEqual(len(self.db.getbooksfortitle(TILE_BOOK)), 3)

        def test_getauthorsbyl(self):
            self.assertEqual(len(self.db.getauthorsbyl(FIRST)), 0)
            book_id1 = self.db.addbook(FILENAME+'1', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            book_id2 = self.db.addbook(FILENAME+'2', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            book_id3 = self.db.addbook(FILENAME+'3', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            author_id1 = self.db.addauthor(FIRST, LAST).author_id
            author_id2 = self.db.addauthor(FIRST, FIRST).author_id
            self.db.addbauthor(book_id1, author_id1)
            self.db.addbauthor(book_id1, author_id2)
            self.db.addbauthor(book_id2, author_id1)
            self.db.addbauthor(book_id3, author_id2)
            rows = self.db.getauthorsbyl(LAST)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][3], 2)
            self.assertEqual(len(self.db.getauthorsbyl(FIRST)), 1)

        def test_getbooksforautor(self):
            self.assertEqual(len(self.db.getbooksforauthor(1)), 0)
            book_id1 = self.db.addbook(FILENAME+'1', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            book_id2 = self.db.addbook(FILENAME+'2', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            book_id3 = self.db.addbook(FILENAME+'3', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            author_id = self.db.addauthor(FIRST, LAST).author_id
            self.db.addbauthor(book_id1, author_id)
            self.db.addbauthor(book_id1, 1)
            self.db.addbauthor(book_id2, author_id)
            self.db.addbauthor(book_id3, 1)
            self.assertEqual(len(self.db.getbooksforauthor(1)), 2)
            self.assertEqual(len(self.db.getbooksforauthor(author_id)), 2)

        def test_getlastbooks(self):
            book_id1 = self.db.addbook(FILENAME+'1', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            time.sleep(1)
            book_id2 = self.db.addbook(FILENAME+'2', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            time.sleep(1)
            book_id3 = self.db.addbook(FILENAME+'3', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            books = self.db.getlastbooks()
            self.assertEqual(len(books), 3)
            self.assertEqual(books[0].book_id, book_id3)
            self.assertEqual(books[1].book_id, book_id2)
            self.assertEqual(books[2].book_id, book_id1)
            self.assertEqual(len(self.db.getlastbooks(2)), 2)

        def test_getgenres_sections(self):
            self.assertEqual(len(self.db.getgenres_sections()), 0)
            book_id1 = self.db.addbook(FILENAME+'1', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            book_id2 = self.db.addbook(FILENAME+'2', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            book_id3 = self.db.addbook(FILENAME+'3', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            genre_id1 = self.db.findgenre('sf_humor')
            genre_id2 = self.db.findgenre('det_classic')
            genre_id3 = self.db.findgenre('sf')
            self.db.addbgenre(book_id1, genre_id1.genre_id)
            self.db.addbgenre(book_id1, genre_id3.genre_id)
            self.db.addbgenre(book_id2, genre_id1.genre_id)
            self.db.addbgenre(book_id3, genre_id2.genre_id)
            rows = self.db.getgenres_sections()
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[1][0], genre_id1)
            self.assertEqual(rows[1][2], 3)
            self.assertEqual(rows[0][0], genre_id2)
            self.assertEqual(rows[0][2], 1)

        def test_getgenres_subsections(self):
            genre_id3 = self.db.findgenre('sf_humor')
            self.assertEqual(len(self.db.getgenres_subsections(genre_id3)), 0)
            book_id1 = self.db.addbook(FILENAME+'1', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            book_id2 = self.db.addbook(FILENAME+'2', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            book_id3 = self.db.addbook(FILENAME+'3', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            genre_id1 = self.db.findgenre('sf_history')
            genre_id2 = self.db.findgenre('det_classic')
            self.db.addbgenre(book_id1, genre_id1)
            self.db.addbgenre(book_id1, genre_id3)
            self.db.addbgenre(book_id2, genre_id1)
            self.db.addbgenre(book_id3, genre_id2)
            rows = self.db.getgenres_subsections(genre_id1)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0][0], genre_id1)
            self.assertEqual(rows[0][2], 2)
            self.assertEqual(rows[1][0], genre_id3)
            self.assertEqual(rows[1][2], 1)

        def test_getbooksforgenre(self):
            genre_id3 = self.db.findgenre('sf_humor')
            self.assertEqual(len(self.db.getbooksforgenre(genre_id3)), 0)
            book_id1 = self.db.addbook(FILENAME+'1', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            book_id2 = self.db.addbook(FILENAME+'2', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            book_id3 = self.db.addbook(FILENAME+'3', PATH_BOOK, 0, '.'+FORMAT, TILE_BOOK, TILE_BOOK, '', 0, 0)
            genre_id1 = self.db.findgenre('sf_history')
            genre_id2 = self.db.findgenre('det_classic')
            self.db.addbgenre(book_id1, genre_id1)
            self.db.addbgenre(book_id1, genre_id3)
            self.db.addbgenre(book_id2, genre_id1)
            self.db.addbgenre(book_id3, genre_id2)
            self.assertEqual(len(self.db.getbooksforgenre(genre_id1)), 2)
            self.assertEqual(len(self.db.getbooksforgenre(genre_id2)), 1)
            self.assertEqual(len(self.db.getbooksforgenre(genre_id3)), 1)

        def test_getdbinfo(self):
            self.assertEqual(self.db.getdbinfo(), (0,1,0))

        def test_zipisscanned(self):
            cat_id = self.db.addcattree(os.path.join(PATH_BOOK, 'file.zip'))
            self.assertEqual(self.db.zipisscanned(os.path.join(PATH_BOOK, 'file.zip')), cat_id)

    unittest.main()
