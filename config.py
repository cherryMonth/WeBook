# coding = utf-8

import os
import configparser
import sys

cf = configparser.ConfigParser()
try:
    cf.read("./system.ini")
    os.environ['owner'] = cf.get("owner", "owner")
    os.environ['database'] = cf.get("database", "database")
    os.environ['port'] = cf.get("port", "port")
    os.environ["ServerConfig"] = cf.get("ServerConfig", "server_listen_port")
except Exception as e:
    print ("config file read failed!", str(e))
    exit(-1)


class ServerConfig(object):
    SECRET_KEY = "hard to guess string"
    MAIL_SERVER = "smtp.qq.com"
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get("EMAIL")
    MAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

    FLASK_MAIL_SENDER = os.environ.get("EMAIL")
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
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://' + os.environ.get("owner") + ':' + os.environ.get("DB_PASSWORD")\
                              + '@' + os.environ.get("DB") + ':' + os.environ.get("port") + "/" + \
                              os.environ.get("database") + "?charset=utf8mb4"

    @staticmethod
    def init_app(app):
        pass


config = {
    "default": ServerConfig
}
