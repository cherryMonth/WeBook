# coding=utf-8

from flaskext.markdown import Markdown
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_mail import Mail
from flask_login import LoginManager
from whoosh.analysis import StemmingAnalyzer
import flask_whooshalchemy


db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.config['WHOOSH_ANALYZER'] = StemmingAnalyzer()
    Markdown(app)
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    from app.main.views import main
    from app.main.auth import auth
    app.register_blueprint(auth)
    app.register_blueprint(main)

    @app.errorhandler(404)
    def page_not_find(e):
        return render_template("error/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("error/500.html"), 500

    return app
