from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy_utils import database_exists, create_database

import os
import logging

logger = logging.getLogger(__name__)

# Get this from ENVIRON VARS (this will be needed for k8s
DB_USER = os.environ["DB_USER"]
DB_PASSWD = os.environ["DB_PASSWD"]
DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ["DB_NAME"]

# Construct DB string
DB_URL = "mysql+mysqlconnector://{user}:{passwd}@{host}/{db}".format(
    user=DB_USER, passwd=DB_PASSWD, host=DB_HOST, db=DB_NAME,
)

engine = create_engine(DB_URL, convert_unicode=True)

if not database_exists(engine.url):
    create_database(engine.url)

Base = declarative_base()
db_session = scoped_session(sessionmaker(bind=engine))
Base.query = db_session.query_property()

#db_session = scoped_session(
#    sessionmaker(autocommit=True, autoflush=True, bind=engine)
#)
