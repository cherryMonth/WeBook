# coding = utf-8

import os
import ConfigParser

cf = ConfigParser.ConfigParser()
try:
    cf.read("./system.ini")
    os.environ['owner'] = cf.get("owner", "owner")
    os.environ['database'] = cf.get("database", "database")
    os.environ['port'] = cf.get("port", "port")
    os.environ["ServerConfig"] = cf.get("ServerConfig", "server_listen_port")
except Exception as e:
    print "config file read failed!", str(e)
    exit(-1)


class ServerConfig(object):
    SECRET_KEY = "hard to guess string"
    MAIL_SERVER = "smtp.qq.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.popen("echo %EMAIL%").read().strip()
    MAIL_PASSWORD = os.popen("echo %EMAIL_PASSWORD%").read().strip()
    FLASK_MAIL_SENDER = os.environ.get("EMAIL")
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = 'mysql://' + os.environ.get("owner") + ':' + os.popen("echo %DB_PASSWORD%").read().strip() + '@' + \
                              os.popen("echo %DB%").read().strip() + ':' + os.environ.get("port") + "/" + os.environ.get("database")

    @staticmethod
    def init_app(app):
        pass


config = {
    "default": ServerConfig
}
