# coding=utf-8
from wtforms import StringField, TextAreaField, SelectMultipleField, SubmitField, PasswordField, BooleanField, FileField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length
from models import Category


class PostForm(FlaskForm):
    title = StringField("", render_kw={'placeholder': u'主题(仅限于30字内...)'})
    text = TextAreaField("", [DataRequired(), Length(max=10000)])
    categories = SelectMultipleField('Categories', coerce=int)
    submit = SubmitField(u"发布文章")

    def __init__(self, title="", text=""):
        super(PostForm, self).__init__()
        if title:
            self.title.data = title
        if text:
            self.text.data = text
        self.categories.choices = [(c.id, c.title) for c in Category.query.order_by('id')]


class FindFile(FlaskForm):
    input = StringField("", render_kw={'placeholder': u'输入您想查找的文章内容...'})
    submit = SubmitField(u"查找")


class FindUser(FlaskForm):
    input = StringField("", render_kw={'placeholder': u'输入您想查找的用户名...'})
    submit = SubmitField(u"查找")


class LoginForm(FlaskForm):
    email = StringField(u"邮箱")
    username = StringField(u'用户名')
    password = PasswordField(u'密码')
    remember_me = BooleanField(u'保持登录')
    submit = SubmitField(u'登录')


class RegisterForm(FlaskForm):
    email = StringField(u'邮箱')
    username = StringField(u'用户名')
    filename = FileField(u"用户头像")
    about_me = TextAreaField(u"个人简介")
    password = PasswordField(u'密码')
    password2 = PasswordField(u'确认密码')
    submit = SubmitField(u'注册')

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)


class ForgetForm(FlaskForm):
    email = StringField(u'邮箱')
    submit = SubmitField(u'提交')


class EditInfoForm(FlaskForm):
    email = StringField(u'邮箱')
    submit = SubmitField(u'提交')


class EditBasic(FlaskForm):
    username = StringField(u'用户名')
    filename = FileField(u"上传用户头像")
    about_me = TextAreaField(u"个人简介")
    user_type = StringField(u'用户身份')
    submit = SubmitField(u'提交')


class EditPassword(FlaskForm):
    old = PasswordField(u"原密码")
    password = PasswordField(u'密码')
    password2 = PasswordField(u'确认密码')
    submit = SubmitField(u'提交')
