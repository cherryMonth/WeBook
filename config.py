# coding = utf-8

import os
import ConfigParser

cf = ConfigParser.ConfigParser()
try:
    cf.read("./system.ini")
    os.environ['owner'] = cf.get("owner", "owner")
    os.environ['database'] = cf.get("database", "database")
    os.environ['port'] = cf.get("port", "port")
    os.environ['password'] = cf.get("password", "password")
    os.environ['host'] = cf.get("host", "host")
    os.environ["ServerConfig"] = cf.get("ServerConfig", "server_listen_port")
except Exception as e:
    print "config file read failed!", str(e)
    exit(-1)


class ServerConfig(object):
    SECRET_KEY = "hard to guess string"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = 'mysql://' + os.environ.get("owner") + ':' + os.environ.get("password") + '@' + \
                              os.environ.get("host") + ':' + os.environ.get("port") + "/" + os.environ.get("database")

    @staticmethod
    def init_app(app):
        pass


config = {
    "default": ServerConfig,
    "html": None
}
