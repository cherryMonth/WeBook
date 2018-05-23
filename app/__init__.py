# coding=utf-8

from flaskext.markdown import Markdown
from flask import Flask, render_template, g, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_mail import Mail
from flask_login import LoginManager, current_user
from whoosh.analysis import StemmingAnalyzer


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
    from app.main.user import user

    @main.before_request
    @user.before_request
    def before_request():
        if current_user.is_active:
            message_nums = len([info for info in current_user.received if info.confirm is False])
            if message_nums > 0:
                g.message_nums = message_nums
            else:
                g.message_nums = None
        else:
            return redirect(url_for('auth.login'))

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(user)

    @app.errorhandler(404)
    def page_not_find(e):
        return render_template("error/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("error/500.html"), 500

    return app
