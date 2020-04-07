from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
import os
import logging
from database.stockdatamodel import Dividend, Financial, Valuation, Ratio
from database.base import Base, engine

def init_db():
    
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    #db_session.commit()
    return Base.metadata.create_all(bind=engine)
