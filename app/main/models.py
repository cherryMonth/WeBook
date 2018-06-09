# coding=utf-8

from app import db, login_manager
from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from whoosh.analysis import SimpleAnalyzer
import hashlib


class Permission(object):
    FOLLOW = 0x11  # 关注他人
    COMMENT = 0x02  # 发表评论
    WRITE_ARTICLES = 0x04  # 写文章
    MODERATE_COMMENTS = 0x08  # 管理他人发表的评论
    ADMINISTER = 0x90  # 管理员权限


class Role(db.Model):  # 角色

    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |  # 用户
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),  # 协管员
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)  # 管理员
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
                role.permissions = roles[r][0]
                role.default = roles[r][1]
                db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class Information(db.Model):

    __tablename__ = 'information'

    id = db.Column(db.Integer, primary_key=True)

    launch_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    receive_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    time = db.Column(db.DateTime, nullable=False, default=datetime.now())

    confirm = db.Column(db.Boolean, default=False)

    info = db.Column(db.String(100), nullable=False)


class Favorite(db.Model):
    __tablename__ = 'favorites'

    favorite_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    favorited_id = db.Column(db.Integer, db.ForeignKey("category.id"), primary_key=True)
    update_time = db.Column(db.DateTime, nullable=False, default=datetime.now())


class Comment(db.Model):
    __tablename__ = "comment"

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    body = db.Column(db.String(150), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now())
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)  # 哪篇文章
    # disabled = db.Column(db.Boolean, default=False)  # 是否隐藏


class Category(db.Model):

    __tablename__ = "category"
    __searchable__ = ['title', 'content']
    __analyzer__ = SimpleAnalyzer()

    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    user = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(30), nullable=False)
    content = db.Column(db.Text(100000), nullable=False)
    update_time = db.Column(db.DateTime, nullable=False, default=datetime.now())
    collect_num = db.Column(db.Integer(), default=0, nullable=False)
    commented = db.relationship('Comment',  # 记录文章的评论数
                               backref=db.backref('post', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    favorite = db.relationship('Favorite',  # 关注这篇文章的人
                               foreign_keys=[Favorite.favorited_id],
                               backref=db.backref('favorited', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    def __repr__(self):

        data = {
            'title': self.title,
            'content': self.content
        }
        return str(data)


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now())


class User(db.Model, UserMixin):

    __tablename__ = 'users'

    __searchable__ = ['email', 'username']

    id = db.Column(db.Integer(), primary_key=True, nullable=False)

    email = db.Column(db.String(64), unique=True, index=True)  # 添加索引

    confirmed = db.Column(db.Boolean, default=False)

    image_name = db.Column(db.String(20), unique=True)

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    username = db.Column(db.String(20), nullable=False, unique=True)

    password_hash = db.Column(db.String(128), nullable=False)

    about_me = db.Column(db.String(100), default="")

    last_seen = db.Column(db.DateTime(), default=datetime.now())

    avatar_hash = db.Column(db.String(32))

    follow_num = db.Column(db.Integer, default=0)  # 总粉丝数

    collect_num = db.Column(db.Integer, default=0)  # 总收藏数

    followed = db.relationship('Follow',  # 用户关注的人
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    followers = db.relationship('Follow',  # 关注用户的人
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    favorite = db.relationship('Favorite',  # 他收藏的文章
                               foreign_keys=[Favorite.favorite_id],
                               backref=db.backref('favorite', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    launched = db.relationship('Information',  # 用户关注的人
                               foreign_keys=[Information.launch_id],
                               backref=db.backref('launched', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    received = db.relationship('Information', foreign_keys=[Information.receive_id],
                               backref=db.backref('received', lazy='joined'), lazy='dynamic',
                               cascade='all, delete-orphan')

    def __repr__(self):
        data = {
            'email': self.email,
            'username': self.username
        }

        return str(data)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASK_MAIL_SENDER']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()
        # self.followed.append(Follow(followed=self))

    @property
    def password(self):  # 密码只能被设置而不能读取
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=600):

        '''

            :param expiration:  # 设置参数令牌的过期时间
            :return 返回加密的签名:
        '''

        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})  # 把自己的id进行加密

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except Exception as e:
            print str(e)
            return False
        if data.get('confirm') != self.id:  # 若解密后不相同则验证失败
            return False
        self.confirmed = True
        from app import db
        db.session.add(self)
        db.session.commit()
        return True

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            from app import db
            user.follow_num += 1
            db.session.add(user)
            db.session.add(f)
            db.session.commit()

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            from app import db
            user.follow_num -= 1
            db.session.add(user)
            db.session.delete(f)
            db.session.commit()

    def ping(self):
        self.last_seen = datetime.now()
        from app import db
        # 之所以在这里加上 import db 是因为要使用同一个db对象 如果不引用将会在多个会话中出现不同的db对象 编译器将会报错
        db.session.add(self)
        db.session.commit()

    def is_following(self, user):
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(
            follower_id=user.id).first() is not None


class AnonymousUser(AnonymousUserMixin):
    role_id = 3

    @staticmethod
    def can():
        return False

    @staticmethod
    def is_administrator():
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
