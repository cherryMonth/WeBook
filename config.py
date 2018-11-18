# coding = utf-8

import os
import ConfigParser
import sys

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
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = "sj1115064450@vip.qq.com"
    MAIL_PASSWORD = "sblmvxvballigaea"

    FLASK_MAIL_SENDER = "sj1115064450@vip.qq.com"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    path = sys.path[0]
    if os.path.isdir(path):
        UPLOAD_FOLDER = path + u"/images/"
    else:
        UPLOAD_FOLDER = os.path.dirname(path) + u"/images/"
    if os.path.isdir(path):
        PAGE_UPLOAD_FOLDER = path + u"/page_images/"
    else:
        PAGE_UPLOAD_FOLDER = os.path.dirname(path) + u"/page_images/"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = 'mysql://root:123456@127.0.0.1:3306/markdown'

    @staticmethod
    def init_app(app):
        pass


config = {
    "default": ServerConfig
}
