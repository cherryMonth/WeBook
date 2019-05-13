from app import create_app
from tornado.options import options, define
from tornado.ioloop import IOLoop
import os
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from app import db
from app.main.models import Role
import flask_whooshalchemy as whooshalchemy
from app.main.models import Category, User

app = create_app("default")

define(name="port", default=os.environ.get("ServerConfig"), type=int)


def createdb():
    with app.app_context():
        db.create_all()
        Role.insert_roles()


createdb()

whooshalchemy.whoosh_index(app, Category)
whooshalchemy.whoosh_index(app, User)

print ('Server running on http://localhost:%s' % options.port)
http_server = HTTPServer(WSGIContainer(app))
http_server.listen(options.port)
IOLoop.instance().start()
