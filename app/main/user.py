# coding=utf-8

from flask import render_template, redirect, flash, url_for
from flask import Blueprint
from forms import FindUser
from models import User, Information
from app import db
from flask_login import login_required, current_user
from sqlalchemy import text

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


@user.route("/information", methods=['GET', 'POST'])
@login_required
def information():
    info_list = Information.query.filter_by(receive_id=current_user.id).all()
    for index in range(len(info_list)):
        info_list[index].author = User.query.filter_by(id=info_list[index].launch_id).first()
    return render_template("information.html", info_list=info_list, length=len(info_list))


@user.route("/info_confirm/<key>", methods=['GET', 'POST'])
@login_required
def confirm(key):
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
    return redirect(url_for("user.information"))


@user.route("/del_info/<key>", methods=['GET', 'POST'])
@login_required
def del_info(key):
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
    return redirect(url_for("user.information"))


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
