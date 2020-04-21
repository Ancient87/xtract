import os

# uncomment the line below for postgres database url from environment variable
# postgres_local_base = os.environ['DATABASE_URL']

basedir = os.path.abspath(os.path.dirname(__file__))

APP_HOST = os.environ["APP_HOST"]
APP_PORT = os.environ["APP_PORT"]

# Get this from ENVIRON VARS (this will be needed for k8s
DB_USER = os.environ["DB_USER"]
DB_PASSWD = os.environ["DB_PASSWD"]
DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ["DB_NAME"]

# Construct DB string
PROD_DB_URL = "mysql+mysqlconnector://{user}:{passwd}@{host}/{db}".format(
    user=DB_USER, passwd=DB_PASSWD, host=DB_HOST, db=DB_NAME,
)

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'Glumanda87!')
    DEBUG = False


class DevelopmentConfig(Config):
    # uncomment the line below to use postgres
    # SQLALCHEMY_DATABASE_URI = postgres_local_base
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = PROD_DB_URL
    #SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'flask_boilerplate_main.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_RUN_PORT = APP_PORT

class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'flask_boilerplate_test.db')
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    DEBUG = False
    # uncomment the line below to use postgres
    SQLALCHEMY_DATABASE_URI = PROD_DB_URL

config_by_name = dict(
    dev=DevelopmentConfig,
    test=TestingConfig,
    prod=ProductionConfig
)

key = Config.SECRET_KEY