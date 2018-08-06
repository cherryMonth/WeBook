# coding=utf-8

from flask import send_from_directory, render_template, redirect, flash, url_for, request
from flask import Blueprint, current_app, session
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from ..email import send_email
import os
from forms import LoginForm, RegisterForm, ForgetForm
from models import User

auth = Blueprint("auth", __name__)


@auth.before_app_request  # 添加对未验证用户的惩罚
def before_request():
    '''
    request.endpoint 是函数和url的映射 url_for是通过endpoint查询url地址，然后找视图函数
    当用户已经登录且未验证且访问的蓝图不是auth就会触发以下函数
    如 url_for('auth.unconfirmed') 中的 auth.unconfirmed 就是一个endpoint
    :return:
    '''
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint \
                and request.endpoint not in ['static', 'main.show_image'] \
                and request.endpoint[:5] != 'auth.':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email([current_user.email], u'核实您的账户',
               'auth/email/confirm', user=current_user, token=token)
    flash(u'一封新的验证邮件已经发送到您的邮箱!', "success")
    return redirect(url_for('main.index'))


@auth.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == "POST":
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(url_for("main.index"))
        flash(u"用户名不存在或密码验证失败,请检查您的输入!", "warning")
    return render_template("auth/login.html", form=form)


@auth.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == "POST":

        if User.query.filter_by(email=form.email.data).first():
            flash(form.email.data + u'已经被注册,请选择其他邮箱!', "warning")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(username=form.username.data).first():
            flash(form.username.data + u'已经被注册,请选择其他用户名!', "warning")
            return redirect(url_for("auth.register"))

        _file = request.files['filename']
        _type = _file.filename.split(".")[-1].lower()

        if not _type or _type not in ['jpeg', 'jpg', 'bmp', "png"]:
            flash(u"图片格式错误，当前只支持'jpeg', 'jpg', 'bmp', 'png'!", "warning")
            return redirect(url_for("main.edit_basic"))

        dirname = current_app.config['UPLOAD_FOLDER']  # 截图存放地点

        user = User(email=form.email.data, username=form.username.data,
                    password=form.password.data, about_me=form.about_me.data)
        db.session.add(user)
        db.session.commit()

        user_id = User.query.filter_by(username=user.username).first().id
        filename = secure_filename(str(user_id) + "." + _type)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
                _file.save(os.path.join(dirname, filename))
            except Exception as e:
                print e
        else:
            _file.save(os.path.join(dirname, filename))
        user.image_name = filename
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email([user.email], u'验证您的账号',
                   'auth/email/confirm', user=user, token=token)
        flash(u"一封验证邮件发送到了你的邮箱,请您验收!", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth.route('/confirm/<token>')  # 当未验证用户点击链接时会跳转到登录页面 并把状态设置为已验证 未验证的用户权限受限
def confirm(token):
    if current_user.is_anonymous:
        user_list = User.query.filter(User.id > 0).all()
        for user in user_list:
            if user.confirm(token):
                login_user(user)
                return redirect(url_for("main.index"))
        flash(u'验证链接无效或已过期。', "warning")
        return redirect(url_for('auth.login'))
    elif current_user.confirm(token):
        return redirect(url_for('main.index'))
    else:
        flash(u'验证链接无效或已过期。', "warning")
        return redirect(url_for('auth.login'))


@auth.route('/login_by_email/<token>')  # 忘记密码后通过邮件跳转到修改信息页面
def login_by_mail(token):
    if current_user.is_anonymous:
        user_list = User.query.filter(User.id > 0).all()
        for user in user_list:
            if user.confirm(token):
                login_user(user)
                session['check'] = "true"
                return redirect(url_for("main.edit_password"))
        flash(u'验证链接无效或已过期。', "warning")
        return redirect(url_for('auth.login'))
    elif current_user.confirm(token):
        session['check'] = "true"
        return redirect(url_for('main.edit_password'))
    else:
        flash(u'验证链接无效或已过期。', "warning")
        return redirect(url_for('auth.login'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash(u'注销成功!', "success")
    return redirect(url_for('main.index'))


@auth.route("/forget", methods=['GET', 'POST'])
def forget():
    form = ForgetForm()
    if request.method == "POST":
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash(u"用户不存在，请检查你的输入!", "warning")
            return redirect(url_for('auth.forget'))

        token = user.generate_confirmation_token()
        send_email([user.email], u'验证您的账号',
                   'auth/email/forget', user=user, token=token)
        print token
        flash(u"一封验证邮件发送到了你的邮箱,请您验收!", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/check_info.html", form=form)


@auth.route("/robots.txt", methods=['GET'])
def get_robots():
    robots_dir = os.getcwd() + "/app/static"
    return send_from_directory(robots_dir, "robots.txt")


@auth.route("/sitemap.xml", methods=['GET'])
def sitemap():
    sitemap_dir = os.getcwd() + "/app/static"
    return send_from_directory(sitemap_dir, "sitemap.xml")
