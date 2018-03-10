# coding = utf-8

from flaskext.markdown import Markdown
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config

db = SQLAlchemy()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    Markdown(app)
    db.init_app(app)
    from app.main.views import main
    app.register_blueprint(main)
    return app
