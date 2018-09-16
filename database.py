
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Get this from ENVIRON VARS (this will be needed for k8s
DB_USER = os.environ['DB_USER']
DB_PASSWD = os.environ['DB_PASSWD']
DB_HOST = os.environ['DB_HOST']
DB_NAME = os.environ['DB_NAME']

# Construct DB string
DB_URL = "mysql+mysqlconnector://{user}:{passwd}@{host}/{db}".format( \
	user = DB_USER, \
	passwd = DB_PASSWD, \
	host = DB_HOST, \
	db = DB_NAME, \
)

engine = create_engine(DB_URL, convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import stockdatamodel
    print("Attempting DB connection to {0}".format(DB_URL))
    return Base.metadata.create_all(bind=engine)
