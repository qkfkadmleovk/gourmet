import sql_db, rdatabase
from pysqlite2 import dbapi2 as sqlite
import os, os.path, re
import gourmet.gglobals as gglobals
from gourmet import keymanager
from gettext import gettext as _


class RecData (sql_db.RecData):

    """SQLite implementation of RecData class, which provides
    Gourmet's interface to the database.
    """

    USE_PAREN_STYLE_REGEXP = True
    
    def __init__ (self, filename=os.path.join(gglobals.gourmetdir,'recipes.db'),db='sqlite'):
        self.filename = filename
        self.db = db
        self.columns = {}
        rdatabase.RecData.__init__(self)

    def setup_table (self, *args,**kwargs):
        name = sql_db.RecData.setup_table(self,*args,**kwargs)
        # Always grab the rowid!
        self.columns[name] = ['rowid']+self.columns[name]
        return name

    def validate_recdic (self, recdic):
        rdatabase.RecData.validate_recdic(self,recdic)
        if recdic.has_key('image'):
            recdic['image']=buffer(recdic['image'])
        if recdic.has_key('thumb'):
            recdic['thumb']=buffer(recdic['thumb'])

    # Main methods we implement
    def initialize_connection (self):
        if os.path.exists(self.filename):
            self.new_db = False
        else:
            self.new_db = True
        if not os.path.exists(os.path.split(self.filename)[0]):
            os.makedirs(os.path.split(self.filename)[0])
        self.connection = sqlite.connect(self.filename)#,isolation_level="IMMEDIATE")
        self.cursor = self.connection.cursor()
        # Create regexp function, based on example at
        # http://lists.initd.org/pipermail/pysqlite/2005-November/000253.html
        def regexp(expr, item):
            if item:
                return re.search(expr,item,re.IGNORECASE) is not None
            else:
                return False
        def instr(s,subs): return s.lower().find(subs.lower())+1
        self.connection.create_function('regexp',2,regexp)
        self.connection.create_function('instr',2,instr)        

    def save (self):
        rdatabase.RecData.save(self) # Do anything generic...
        self.connection.commit()
        self.changed = False

    def check_for_table (self, name):
        self.cursor.execute('SELECT name FROM sqlite_master WHERE NAME=?',[name])
        if self.cursor.fetchall(): return True
        else: return False

    def new_id (self):
        """Reserve a new_id

        We have to create the recipe to reserve the ID, so this is
        really not a good method to call unless necessary.
        """
        self.cursor.execute('SELECT seq FROM SQLITE_SEQUENCE WHERE name="%s"'%self.rview)
        row = self.cursor.fetchone()
        if row:
            idval = row[0]+1
            self.cursor.execute('UPDATE SQLITE_SEQUENCE SET seq=%s WHERE name="%s"'%(idval,self.rview))
        else:
            idval = 1
            self.cursor.execute('INSERT INTO SQLITE_SEQUENCE (seq,name) VALUES (%s,"%s")'%(idval,self.rview))
        return idval

class RecipeManager (RecData,rdatabase.RecipeManager):
    def __init__ (self, file=os.path.join(gglobals.gourmetdir,'recipes.db')):
        RecData.__init__(self,filename=file)
        self.km = keymanager.KeyManager(rm=self)

class dbDic (rdatabase.dbDic):
    pass

if __name__ == '__main__':
    import tempfile
    rd = RecData(filename=tempfile.mktemp(".db"))
    #rd = RecData()
    rdatabase.test_db(rd)
    #rd.add_rec({'title':'Spaghetti','cuisine':'Italian','rating':5})
    #rec = rd.add_rec({'title':'Grilled Cheese','cuisine':'American','rating':8})
    #rd.add_ing({'id':rec.id,'item':'Cheese','ingkey':'cheese','amount':2,'unit':'slices'})
    #rd.add_ing({'id':rec.id,'item':'Bread','ingkey':'bread','amount':2,'unit':'slices'})
    #rd.add_ing({'id':rec.id,'item':'Butter','ingkey':'butter, salted','amount':2,'unit':'pats'})
    #rec = rd.add_rec({'title':'Pop Tarts','servings':4,'category':'junk food, high fat','cuisine':'American'})
    #rd.add_ing({'id':rec.id,'item':'Pop tarts','amount':1,'unit':'box','ingkey':'pop tarts'})
