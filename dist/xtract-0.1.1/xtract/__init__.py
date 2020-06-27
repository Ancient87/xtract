from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import connexion
from connexion.resolver import RestyResolver

from .config import config_by_name

db = SQLAlchemy()
flask_bcrypt = Bcrypt()


def create_app(config_name):
    app_connex = connexion.App(__name__, specification_dir="api")
    app = app_connex.app
    
    app_connex.add_api("xtract_api_spec.yaml", resolver=RestyResolver("xtract.api"))
    application = app

    app.config.from_object(config_by_name[config_name])
    db.init_app(app)
    flask_bcrypt.init_app(app)

    return (app, app_connex, config_by_name[config_name].APP_PORT)
    
prod_app = create_app("prod")[0]