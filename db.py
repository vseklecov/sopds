# -*- coding: utf-8 -*-
__author__ = 'vseklecov'

from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sql
import sqlalchemy.orm as orm

Base = declarative_base()

book_authors = sql.Table('bauthors',
                         Base.metadata,
                         sql.Column('author_id', sql.ForeignKey('authors.author_id')),
                         sql.Column('book_id', sql.ForeignKey('books.book_id')))

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

    def __repr__(self):
        return "<Catalog('%s')>" % self.cat_name


class Author(Base):
    __tablename__ = 'authors'

    author_id = sql.Column(sql.Integer, sql.Sequence('author_id_seq'), primary_key=True)
    first_name = sql.Column(sql.String(64))
    last_name = sql.Column(sql.String(64))

    sql.Index('fullname', last_name, first_name)

    def __init__(self, author_id, last_name, first_name=''):
        self.author_id = author_id
        self.last_name = last_name
        self.first_name = first_name

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

    def __init__(self, iname='sqlite:///sopds.db', iuser='', ipass='', ihost='localhost', iroot_lib='..'):
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
        book = self.session.query(Book).\
            filter(Book.filename == name).\
            filter(Book.path == path).\
            first()
        if not book:
            book_id = 0
        else:
            book_id = book.book_id
        return book_id

    def finddouble(self, title, format_book, file_size):
        book = self.session.query(Book).\
            filter(Book.title == title).\
            filter(Book.format == format_book).\
            filter(Book.filesize == file_size).\
            filter(Book.doublicat == 0).\
            first()
        if not book:
            book_id = 0
        else:
            book_id = book.book_id
        return book_id

    def addbook(self, name, path, cat_id, exten, title, lang, size=0, archive=0, doublicates=0):
        book_id = self.findbook(name, path)
        if book_id != 0:
            return book_id
        format = exten[1:]
        format = format.lower()
        if doublicates != 0:
            doublicat = self.finddouble(title, format, size)
        else:
            doublicat = 0
        book = Book(name, path, cat_id, exten, title, lang, size, archive, doublicates)
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
        author = self.session.query(Author).\
            filter(sql.func.lower(Author.first_name) == first_name.lower()).\
            filter(sql.func.lower(Author.last_name) == last_name.lower()).\
            first()
        if not author:
            author_id = 0
        else:
            author_id = author.author_id
        return author_id

    def findbauthor(self, book_id, author_id):
        sql_findbauthor=("select book_id from "+TBL_BAUTHORS+" where book_id=%s and author_id=%s")
        data_findbauthor=(book_id,author_id)
        cursor=self.cnx.cursor()
        cursor.execute(sql_findbauthor,data_findbauthor)
        row=cursor.fetchone()
        result=(row!=None)
        cursor.close()
        return result

    def addauthor(self, first_name, last_name):
        author_id=self.findauthor(first_name,last_name)
        if author_id!=0:
            return author_id
        sql_addauthor=("insert into "+TBL_AUTHORS+"(first_name,last_name) VALUES(%s,%s)")
        data_addauthor=(first_name,last_name)
        cursor=self.cnx.cursor()
        cursor.execute(sql_addauthor,data_addauthor)
        author_id=cursor.lastrowid
        self.cnx.commit()
        cursor.close()
        return author_id

    def addbauthor(self, book_id, author_id):
        sql_addbauthor=("insert into "+TBL_BAUTHORS+"(book_id,author_id) VALUES(%s,%s)")
        data_addbauthor=(book_id,author_id)
        cursor=self.cnx.cursor()
        try:
            cursor.execute(sql_addbauthor,data_addbauthor)
            self.cnx.commit()
        except:
            pass
        finally:
            cursor.close()

    def findgenre(self,genre):
        sql=("select genre_id from "+TBL_GENRES+" where LOWER(genre)='"+genre+"'")
        cursor=self.cnx.cursor()
        cursor.execute(sql)
        row=cursor.fetchone()
        if row==None:
            genre_id=0
        else:
            genre_id=row[0]
        cursor.close()
        return genre_id

    def findbgenre(self, book_id, genre_id):
        sql=("select book_id from "+TBL_BGENRES+" where book_id=%s and genre_id=%s")
        data=(book_id,genre_id)
        cursor=self.cnx.cursor()
        cursor.execute(sql,data)
        row=cursor.fetchone()
        result=(row!=None)
        cursor.close()
        return result

    def addgenre(self, genre):
        genre_id=self.findgenre(genre)
        if genre_id!=0:
            return genre_id
        sql=("insert into "+TBL_GENRES+"(genre,section,subsection) VALUES(%s,%s,%s)")
        data=(genre,unknown_genre,genre)
        cursor=self.cnx.cursor()
        cursor.execute(sql,data)
        genre_id=cursor.lastrowid
        self.cnx.commit()
        cursor.close()
        return genre_id

    def addbgenre(self, book_id, genre_id):
        sql=("insert into "+TBL_BGENRES+"(book_id,genre_id) VALUES(%s,%s)")
        data=(book_id,genre_id)
        cursor=self.cnx.cursor()
        try:
            cursor.execute(sql,data)
            self.cnx.commit()
        except:
            pass
        finally:
            cursor.close()

    def findcat(self, catalog):
        (head,tail)=os.path.split(catalog)
        sql_findcat=("select cat_id from "+TBL_CATALOGS+" where cat_name=%s and path=%s")
        data_findcat=(tail,catalog)
        cursor=self.cnx.cursor()
        cursor.execute(sql_findcat,data_findcat)
        row=cursor.fetchone()
        if row==None:
            cat_id=0
        else:
            cat_id=row[0]
        cursor.close()
        return cat_id

    def addcattree(self, catalog, archive=0):
        cat_id=self.findcat(catalog)
        if cat_id!=0:
            return cat_id
        if catalog=="":
            return 0
        (head,tail)=os.path.split(catalog)
        parent_id=self.addcattree(head)
        sql_addcat=("insert into "+TBL_CATALOGS+"(parent_id,cat_name,path,cat_type) VALUES(%s, %s, %s, %s)")
        data_addcat=(parent_id,tail,catalog,archive)
        cursor=self.cnx.cursor()
        cursor.execute(sql_addcat,data_addcat)
        cat_id=cursor.lastrowid
        self.cnx.commit()
        cursor.close()
        return cat_id

    def getcatinparent(self,parent_id,limit=0,page=0):
        if limit==0:
            limitstr=""
        else:
            limitstr="limit "+str(limit*page)+","+str(limit)
        sql_findcats=("select cat_id,cat_name from "+TBL_CATALOGS+" where parent_id="+str(parent_id)+" order by cat_name "+limitstr)
        cursor=self.cnx.cursor()
        cursor.execute(sql_findcats)
        rows=cursor.fetchall()
        cursor.close
        return rows

    def getbooksincat(self,cat_id,limit=0,page=0):
        if limit==0:
            limitstr=""
        else:
            limitstr="limit "+str(limit*page)+","+str(limit)
        sql_findbooks=("select book_id,filename, path, registerdate from "+TBL_BOOKS+" where cat_id="+str(cat_id)+" order by filename "+limitstr)
        cursor=self.cnx.cursor()
        cursor.execute(sql_findbooks)
        rows=cursor.fetchall()
        cursor.close
        return rows

    def getitemsincat(self,cat_id,limit=0,page=0):
        if limit==0:
            limitstr=""
        else:
            limitstr="limit "+str(limit*page)+","+str(limit)
        sql_finditems=("select SQL_CALC_FOUND_ROWS 1,cat_id,cat_name,path,now(),cat_name as title from "+TBL_CATALOGS+" where parent_id="+str(cat_id)+" union all "
        "select 2,book_id,filename,path,registerdate,title from "+TBL_BOOKS+" where cat_id="+str(cat_id)+" order by 1,6 "+limitstr)
        cursor=self.cnx.cursor()
        cursor.execute(sql_finditems)
        rows=cursor.fetchall()

        cursor.execute("SELECT FOUND_ROWS()")
        found_rows=cursor.fetchone()
        if found_rows[0]>limit*page+limit:
            self.next_page=True
        else:
            self.next_page=False

        cursor.close
        return rows

    def getbook(self,book_id):
        sql_getbook=("select filename, path, registerdate, format, title, cat_type, cover, cover_type, filesize from "+TBL_BOOKS+" where book_id="+str(book_id))
        cursor=self.cnx.cursor()
        cursor.execute(sql_getbook)
        row=cursor.fetchone()
        cursor.close
        return row

    def getauthors(self,book_id):
        sql=("select first_name,last_name from "+TBL_AUTHORS+" a, "+TBL_BAUTHORS+" b where b.author_id=a.author_id and b.book_id="+str(book_id))
        cursor=self.cnx.cursor()
        cursor.execute(sql)
        rows=cursor.fetchall()
        cursor.close
        return rows

    def getgenres(self,book_id):
        sql=("select section, subsection from "+TBL_GENRES+" a, "+TBL_BGENRES+" b where b.genre_id=a.genre_id and b.book_id="+str(book_id))
        cursor=self.cnx.cursor()
        cursor.execute(sql)
        rows=cursor.fetchall()
        cursor.close
        return rows

    def getauthor_2letters(self,letters):
        lc=len(letters)+1
        sql="select UPPER(substring(trim(CONCAT(last_name,' ',first_name)),1,"+str(lc)+")) as letters, count(*) as cnt from "+TBL_AUTHORS+" where UPPER(substring(trim(CONCAT(last_name,' ',first_name)),1,"+str(lc-1)+"))='"+letters+"' group by 1 order by 1"
        cursor=self.cnx.cursor()
        cursor.execute(sql)
        rows=cursor.fetchall()
        cursor.close
        return rows

    def gettitle_2letters(self,letters,doublicates=True):
        if doublicates:
            dstr=''
        else:
            dstr=' and doublicat=0 '
        lc=len(letters)+1
        sql="select UPPER(substring(trim(title),1,"+str(lc)+")) as letteris, count(*) as cnt from "+TBL_BOOKS+" where UPPER(substring(trim(title),1,"+str(lc-1)+"))='"+letters+"' "+dstr+" group by 1 order by 1"
        cursor=self.cnx.cursor()
        cursor.execute(sql)
        rows=cursor.fetchall()
        cursor.close
        return rows

    def getbooksfortitle(self,letters,limit=0,page=0,doublicates=True):
        if limit==0:
            limitstr=""
        else:
            limitstr="limit "+str(limit*page)+","+str(limit)
        if doublicates:
            dstr=''
        else:
            dstr=' and doublicat=0 '
        sql="select SQL_CALC_FOUND_ROWS book_id,filename,path,registerdate,title,cover,cover_type from "+TBL_BOOKS+" where title like '"+letters+"%' "+dstr+" order by title "+limitstr
        cursor=self.cnx.cursor()
        cursor.execute(sql)
        rows=cursor.fetchall()

        cursor.execute("SELECT FOUND_ROWS()")
        found_rows=cursor.fetchone()
        if found_rows[0]>limit*page+limit:
            self.next_page=True
        else:
            self.next_page=False

        cursor.close
        return rows

    def getauthorsbyl(self,letters,limit=0,page=0,doublicates=True):
        if limit==0:
           limitstr=""
        else:
           limitstr="limit "+str(limit*page)+","+str(limit)
        if doublicates:
           dstr=''
        else:
           dstr=' and c.doublicat=0 '
        sql="select SQL_CALC_FOUND_ROWS a.author_id, a.first_name, a.last_name, count(*) as cnt from "+TBL_AUTHORS+" a, "+TBL_BAUTHORS+" b, "+TBL_BOOKS+" c where a.author_id=b.author_id and b.book_id=c.book_id and UPPER(a.last_name) like '"+letters+"%' "+dstr+" group by 1,2,3 order by 3,2 "+limitstr
        cursor=self.cnx.cursor()
        cursor.execute(sql)
        rows=cursor.fetchall()

        cursor.execute("SELECT FOUND_ROWS()")
        found_rows=cursor.fetchone()
        if found_rows[0]>limit*page+limit:
           self.next_page=True
        else:
           self.next_page=False

        cursor.close
        return rows

    def getbooksforautor(self,author_id,limit=0,page=0,doublicates=True):
        if limit==0:
           limitstr=""
        else:
           limitstr="limit "+str(limit*page)+","+str(limit)
        if doublicates:
           dstr=''
        else:
           dstr=' and a.doublicat=0 '
        sql="select SQL_CALC_FOUND_ROWS a.book_id,a.filename,a.path,a.registerdate,a.title,a.cover,a.cover_type from "+TBL_BOOKS+" a, "+TBL_BAUTHORS+" b where a.book_id=b.book_id and b.author_id="+str(author_id)+dstr+" order by a.title "+limitstr
        cursor=self.cnx.cursor()
        cursor.execute(sql)
        rows=cursor.fetchall()

        cursor.execute("SELECT FOUND_ROWS()")
        found_rows=cursor.fetchone()
        if found_rows[0]>limit*page+limit:
           self.next_page=True
        else:
           self.next_page=False

        cursor.close
        return rows

    def getlastbooks(self,limit=0):
        if limit==0:
           limitstr=""
        else:
           limitstr="limit "+str(limit)
        sql="select book_id,filename,path,registerdate,title from "+TBL_BOOKS+" order by registerdate desc "+limitstr
        cursor=self.cnx.cursor()
        cursor.execute(sql)
        rows=cursor.fetchall()
        cursor.close
        return rows

    def getgenres_sections(self):
        sql="select min(a.genre_id), a.section, count(*) as cnt from "+TBL_GENRES+" a, "+TBL_BGENRES+" b where a.genre_id=b.genre_id group by a.section order by a.section"
        cursor=self.cnx.cursor()
        cursor.execute(sql)
        rows=cursor.fetchall()
        cursor.close
        return rows

    def getgenres_subsections(self,section_id):
        sql="select a.genre_id, a.subsection, count(*) as cnt from "+TBL_GENRES+" a, "+TBL_BGENRES+" b where a.genre_id=b.genre_id and section in (select section from "+TBL_GENRES+" where genre_id="+str(section_id)+") group by a.subsection order by a.subsection"
        cursor=self.cnx.cursor()
        cursor.execute(sql)
        rows=cursor.fetchall()
        cursor.close
        return rows

    def getbooksforgenre(self,genre_id,limit=0,page=0,doublicates=True):
        if limit==0:
           limitstr=""
        else:
           limitstr="limit "+str(limit*page)+","+str(limit)
        if doublicates:
           dstr=''
        else:
           dstr=' and a.doublicat=0 '
        sql="select SQL_CALC_FOUND_ROWS a.book_id,a.filename,a.path,a.registerdate,a.title,a.cover,a.cover_type from "+TBL_BOOKS+" a, "+TBL_BGENRES+" b where a.book_id=b.book_id and b.genre_id="+str(genre_id)+dstr+" order by a.lang desc, a.title "+limitstr
        cursor=self.cnx.cursor()
        cursor.execute(sql)
        rows=cursor.fetchall()

        cursor.execute("SELECT FOUND_ROWS()")
        found_rows=cursor.fetchone()
        if found_rows[0]>limit*page+limit:
           self.next_page=True
        else:
           self.next_page=False

        cursor.close
        return rows

    def getdbinfo(self,doublicates=True):
        if doublicates:
           dstr=''
        else:
           dstr=' where doublicat=0 '
        sql="select count(*) from %s %s union select count(*) from %s union select count(*) from %s"%(TBL_BOOKS,dstr,TBL_AUTHORS,TBL_CATALOGS)
        cursor=self.cnx.cursor()
        cursor.execute(sql)
        rows=cursor.fetchall()
        return rows

    def zipisscanned(self,zipname):
        sql='select cat_id from '+TBL_CATALOGS+' where path="'+zipname+'" limit 1'
        cursor=self.cnx.cursor()
        cursor.execute(sql)
        row=cursor.fetchone()
        if row==None:
           cat_id=0
        else:
           cat_id=row[0]
        return cat_id

    def __del__(self):
        self.closeDB()



def init_db(path):
    """
    Инициализация базы данных

    """
    engine = sql.create_engine(path)
    Base.metadata.create_all(engine)
    Session = orm.sessionmaker(bind=engine)
    session = Session()
    session.add(Author(1, 'Неизвестный автор'))
    session.commit()

    session.add(Genre("sf_history", "Альтернативная история", "Фантастика"))
    session.add(Genre("sf_action", "Боевая фантастика", "Фантастика"))
    session.add(Genre("sf_epic", "Эпическая фантастика", "Фантастика"))
    session.add(Genre("sf_heroic", "Героическая фантастика", "Фантастика"))
    session.add(Genre("sf_detective", "Детективная фантастика", "Фантастика"))
    session.add(Genre("sf_cyberpunk", "Киберпанк", "Фантастика"))
    session.add(Genre("sf_space", "Космическая фантастика", "Фантастика"))
    session.add(Genre("sf_social", "Социально психологическая фантастика", "Фантастика"))
    session.add(Genre("sf_horror", "Ужасы и Мистика", "Фантастика"))
    session.add(Genre("sf_humor", "Юмористическая фантастика", "Фантастика"))
    session.add(Genre("sf_fantasy", "Фэнтези", "Фантастика"))
    session.add(Genre("sf", "Научная Фантастика", "Фантастика"))
    session.add(Genre("det_classic", "Классический детектив", "Детективы и Триллеры"))
    session.add(Genre("det_police", "Полицейский детектив", "Детективы и Триллеры"))
    session.add(Genre("det_action", "Боевик", "Детективы и Триллеры"))
    session.add(Genre("det_irony", "Иронический детектив", "Детективы и Триллеры"))
    session.add(Genre("det_history", "Исторический детектив", "Детективы и Триллеры"))
    session.add(Genre("det_espionage", "Шпионский детектив", "Детективы и Триллеры"))
    session.add(Genre("det_crime", "Криминальный детектив", "Детективы и Триллеры"))
    session.add(Genre("det_political", "Политический детектив", "Детективы и Триллеры"))
    session.add(Genre("det_maniac", "Маньяки", "Детективы и Триллеры"))
    session.add(Genre("det_hard", "Крутой детектив", "Детективы и Триллеры"))
    session.add(Genre("thriller", "Триллер", "Детективы и Триллеры"))
    session.add(Genre("detective", "Детектив (не относящийся в прочие категории).", "Детективы и Триллеры"))
    session.add(Genre("prose_classic", "Классическая проза", "Проза"))
    session.add(Genre("prose_history", "Историческая проза", "Проза"))
    session.add(Genre("prose_contemporary", "Современная проза", "Проза"))
    session.add(Genre("prose_counter", "Контркультура", "Проза"))
    session.add(Genre("prose_rus_classic", "Русская классическая проза", "Проза"))
    session.add(Genre("prose_su_classics", "Советская классическая проза", "Проза"))
    session.add(Genre("love_contemporary", "Современные любовные романы", "Любовные романы"))
    session.add(Genre("love_history", "Исторические любовные романы", "Любовные романы"))
    session.add(Genre("love_detective", "Остросюжетные любовные романы", "Любовные романы"))
    session.add(Genre("love_short", "Короткие любовные романы", "Любовные романы"))
    session.add(Genre("love_erotica", "Эротика", "Любовные романы"))
    session.add(Genre("adv_western", "Вестерн", "Приключения"))
    session.add(Genre("adv_history", "Исторические приключения", "Приключения"))
    session.add(Genre("adv_indian", "Приключения про индейцев", "Приключения"))
    session.add(Genre("adv_maritime", "Морские приключения", "Приключения"))
    session.add(Genre("adv_geo", "Путешествия и география", "Приключения"))
    session.add(Genre("adv_animal", "Природа и животные", "Приключения"))
    session.add(Genre("adventure", "Прочие приключения", "Приключения"))
    session.add(Genre("child_tale", "Сказка", "Детская литература"))
    session.add(Genre("child_verse", "Детские стихи", "Детская литература"))
    session.add(Genre("child_prose", "Детскиая проза", "Детская литература"))
    session.add(Genre("child_sf", "Детская фантастика", "Детская литература"))
    session.add(Genre("child_det", "Детские остросюжетные", "Детская литература"))
    session.add(Genre("child_adv", "Детские приключения", "Детская литература"))
    session.add(Genre("child_education", "Детская образовательная литература", "Детская литература"))
    session.add(Genre("children", "Прочая детская литература", "Детская литература"))
    session.add(Genre("poetry", "Поэзия", "Поэзия, Драматургия"))
    session.add(Genre("dramaturgy", "Драматургия", "Поэзия, Драматургия"))
    session.add(Genre("antique_ant", "Античная литература", "Старинное"))
    session.add(Genre("antique_european", "Европейская старинная литература", "Старинное"))
    session.add(Genre("antique_russian", "Древнерусская литература", "Старинное"))
    session.add(Genre("antique_east", "Древневосточная литература", "Старинное"))
    session.add(Genre("antique_myths", "Мифы. Легенды. Эпос", "Старинное"))
    session.add(Genre("antique", "Прочая старинная литература", "Старинное"))
    session.add(Genre("sci_history", "История", "Наука, Образование"))
    session.add(Genre("sci_psychology", "Психология", "Наука, Образование"))
    session.add(Genre("sci_culture", "Культурология", "Наука, Образование"))
    session.add(Genre("sci_religion", "Религиоведение", "Наука, Образование"))
    session.add(Genre("sci_philosophy", "Философия", "Наука, Образование"))
    session.add(Genre("sci_politics", "Политика", "Наука, Образование"))
    session.add(Genre("sci_business", "Деловая литература", "Наука, Образование"))
    session.add(Genre("sci_juris", "Юриспруденция", "Наука, Образование"))
    session.add(Genre("sci_linguistic", "Языкознание", "Наука, Образование"))
    session.add(Genre("sci_medicine", "Медицина", "Наука, Образование"))
    session.add(Genre("sci_phys", "Физика", "Наука, Образование"))
    session.add(Genre("sci_math", "Математика", "Наука, Образование"))
    session.add(Genre("sci_chem", "Химия", "Наука, Образование"))
    session.add(Genre("sci_biology", "Биология", "Наука, Образование"))
    session.add(Genre("sci_tech", "Технические науки", "Наука, Образование"))
    session.add(Genre("science", "Прочая научная литература", "Наука, Образование"))
    session.add(Genre("comp_www", "Интернет", "Компьютеры и Интернет"))
    session.add(Genre("comp_programming", "Программирование", "Компьютеры и Интернет"))
    session.add(Genre("comp_hard", "Компьютерное железо", "Компьютеры и Интернет"))
    session.add(Genre("comp_soft", "Программы", "Компьютеры и Интернет"))
    session.add(Genre("comp_db", "Базы данных", "Компьютеры и Интернет"))
    session.add(Genre("comp_osnet", "ОС и Сети", "Компьютеры и Интернет"))
    session.add(Genre("computers", "Прочая околокомпьтерная литература", "Компьютеры и Интернет"))
    session.add(Genre("ref_encyc", "Энциклопедии", "Справочная литература"))
    session.add(Genre("ref_dict", "Словари", "Справочная литература"))
    session.add(Genre("ref_ref", "Справочники", "Справочная литература"))
    session.add(Genre("ref_guide", "Руководства", "Справочная литература"))
    session.add(Genre("reference", "Прочая справочная литература", "Справочная литература"))
    session.add(Genre("nonf_biography", "Биографии и Мемуары", "Документальная литература"))
    session.add(Genre("nonf_publicism", "Публицистика", "Документальная литература"))
    session.add(Genre("nonf_criticism", "Критика", "Документальная литература"))
    session.add(Genre("design", "Искусство и Дизайн", "Документальная литература"))
    session.add(Genre("nonfiction", "Прочая документальная литература", "Документальная литература"))
    session.add(Genre("religion_rel", "Религия", "Религия и духовность"))
    session.add(Genre("religion_esoterics", "Эзотерика", "Религия и духовность"))
    session.add(Genre("religion_self", "Самосовершенствование", "Религия и духовность"))
    session.add(Genre("religion", "Прочая религионая литература", "Религия и духовность"))
    session.add(Genre("humor_anecdote", "Анекдоты", "Юмор"))
    session.add(Genre("humor_prose", "Юмористическая проза", "Юмор"))
    session.add(Genre("humor_verse", "Юмористические стихи", "Юмор"))
    session.add(Genre("humor", "Прочий юмор", "Юмор"))
    session.add(Genre("home_cooking", "Кулинария", "Дом и семья"))
    session.add(Genre("home_pets", "Домашние животные", "Дом и семья"))
    session.add(Genre('home_crafts', "Хобби и ремесла", "Дом и семья"))
    session.add(Genre("home_entertain", "Развлечения", "Дом и семья"))
    session.add(Genre("home_health", "Здоровье", "Дом и семья"))
    session.add(Genre("home_garden", "Сад и огород", "Дом и семья"))
    session.add(Genre("home_diy", "Сделай сам", "Дом и семья"))
    session.add(Genre("home_sport", "Спорт", "Дом и семья"))
    session.add(Genre("home_sex", "Эротика, Секс", "Дом и семья"))
    session.add(Genre("home", "Прочее домоводство", "Дом и семья"))
    session.commit()


if __name__ == '__main__':
    import sys
    init_db('sqlite:///'+sys.argv[1])
