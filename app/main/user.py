# coding=utf-8

from flask import render_template, redirect, flash, url_for, request, abort
from flask import Blueprint, current_app, send_from_directory
import os
from app.main.forms import FindUser
from app.main.models import User, Information
from app import db
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from sqlalchemy import text
import json

user = Blueprint("user", __name__)


@user.route("/find_user", methods=['POST', 'GET'])
def find_user():
    form = FindUser()

    hot_user_list = User.query.from_statement(
        text("SELECT * FROM markdown.users ORDER BY collect_num DESC LIMIT 5 ;")).all()

    if form.validate_on_submit():
        user_list = User.query.whoosh_search(form.input.data).all()

        length = len(user_list)
        if not user_list:
            flash(u"没有找到符合要求的用户!", "warning")
            return redirect(url_for("user.find_user"))

        return render_template("find_user.html", form=form, user_list=user_list, length=length)
    return render_template("find_user.html", form=form, hot_user_list=hot_user_list)


@user.route("/followed_user/<key>", methods=['GET', 'POST'])
@login_required
def followed_user(key):
    _user = User.query.filter_by(id=key).first()
    if not _user:
        flash(u"用户不存在!", "warning")
    elif current_user.is_following(_user):
        flash(u"您已经关注了此用户，无法重复关注!", "warning")
    else:
        current_user.follow(_user)
        _info = Information()
        _info.launch_id = current_user.id
        _info.receive_id = _user.id
        _info.info = u"用户" + current_user.username + u" 对您进行了关注!"
        db.session.add(_info)
        flash(u"关注成功!", "success")
    return redirect(url_for("user.find_user"))


@user.route("/unfollowed_user/<key>", methods=['GET', 'POST'])
@login_required
def unfollowed_user(key):
    _user = User.query.filter_by(id=key).first()
    if not _user:
        flash(u"用户不存在!", "warning")
    elif not current_user.is_following(_user):
        flash(u"您尚未关注此用户，无法取消关注!", "warning")
    else:
        _info = Information()
        _info.launch_id = current_user.id
        _info.receive_id = _user.id
        _info.info = u"用户" + current_user.username + u" 对您取消了关注!"
        db.session.add(_info)
        current_user.unfollow(_user)
        flash(u"取消关注成功!", "success")
    return redirect(url_for("user.find_user"))


@user.route("/information/<int:page>", methods=['GET', 'POST'])
@login_required
def information(page):
    temp = Information.query.filter_by(receive_id=current_user.id)
    info_list = temp.order_by(Information.time.desc()).paginate(page, 10, error_out=True).items
    length = len(temp.all())
    page_num = int(length / 10 if length % 10 == 0 else length / 10 + 1)
    for index in range(len(info_list)):
        info_list[index].author = User.query.filter_by(id=info_list[index].launch_id).first()
    return render_template("information.html", info_list=info_list, length=length, page=page, page_num=page_num)


@user.route("/info_confirm/<int:key>/<int:page>", methods=['GET', 'POST'])
@login_required
def confirm(key, page):
    info = Information.query.filter_by(id=key).first()
    if not info:
        flash(u"信息不存在!", "warning")
    elif info.confirm is True:
        flash(u"信息已被忽略，无法再次忽略!", "warning")
    elif info.receive_id != current_user.id:
        flash(u"您不是此信息的接收者，无法忽略此消息!", "warning")
    else:
        info.confirm = True
        flash(u"信息确认成功!", "success")
        db.session.add(info)
        db.session.commit()
    return redirect(url_for("user.information", page=page))


@user.route("/del_info/<int:key>/<int:page>", methods=['GET', 'POST'])
@login_required
def del_info(key, page):
    info = Information.query.filter_by(id=key).first()
    if not info:
        flash(u"信息不存在!", "warning")
    elif info.receive_id != current_user.id:
        flash(u"您不是此信息的接收者，无法删除!", "warning")
    else:
        info.confirm = True
        flash(u"信息删除成功!", "success")
        db.session.delete(info)
        db.session.commit()
    return redirect(url_for("user.information", page=page))


@user.route("/my_follow", methods=['GET', 'POST'])
@login_required
def my_follow():
    users = current_user.followed
    user_list = [User.query.filter_by(id=_user.followed_id).first() for _user in users]
    return render_template("edit/edit_my_follow.html", user_list=user_list)


@user.route("/follow_my", methods=['GET', 'POST'])
@login_required
def follow_me():
    users = current_user.followers
    user_list = [User.query.filter_by(id=_user.follower_id).first() for _user in users]
    return render_template("edit/edit_follow_me.html", user_list=user_list)


@user.route("/get_user_info/", methods=['GET', 'POST'])
def get_user_info():
    key = request.args.get('email') or ""
    password = request.args.get('password')
    _user = User.query.filter_by(email=key).first()
    info = dict()
    if password and _user and _user.verify_password(password):
        # 对象的序列化为字典 info.update(_user.__dict__)
        info['username'] = _user.username
        info['follow_num'] = _user.follow_num
        info['image_name'] = "https://www.webook.mobi/show_image/{}".format(_user.id)
        info['about_me'] = _user.about_me
        info['id'] = _user.id
        info['collect_num'] = _user.collect_num
        info['email'] = _user.email
    return json.dumps(info)


@user.route("/send_info/<int:key>", methods=["POST"])
@login_required
def send_info(key):
    info = Information()
    _user = User.query.filter_by(id=key).first()

    if not _user:
        abort(404)

    info.launch_id = current_user.id
    info.receive_id = _user.id
    info.info = request.form.get('text')
    db.session.add(info)
    db.session.commit()
    flash(u"发送成功!", "success")
    return redirect(url_for("main.index"))


@user.route("/upload_images", methods=['POST', "GET"])
@login_required
def upload_images():
    _file = request.files.get('editormd-image-file')
    result = dict()
    _type = _file.filename.split(".")[-1].lower()
    filename = secure_filename(_file.filename)
    _file.save(os.path.join(current_app.config['PAGE_UPLOAD_FOLDER'], filename))
    if not _type or _type not in ["jpg", "jpeg", "gif", "png", "bmp", "webp"]:
        result['success'] = 0
        result['message'] = u"图片格式错误，当前只支持'jpeg', 'jpg', 'bmp', 'png', 'webp'" \
                            u", 'gif'!"
        result['url'] = None
        return json.dumps(result)
    else:
        result['success'] = 1
        result['message'] = u"上传成功!"
        result['url'] = "http://www.webook.mobi/display_images/{}".format(filename)
        return json.dumps(result)


@user.route("/display_images/<filename>", methods=['GET'])
def display_images(filename):
    if not os.path.exists(current_app.config['PAGE_UPLOAD_FOLDER'] + filename):
        return send_from_directory(current_app.config['PAGE_UPLOAD_FOLDER'], "-1.jpg")
    else:
        return send_from_directory(current_app.config['PAGE_UPLOAD_FOLDER'], filename)
