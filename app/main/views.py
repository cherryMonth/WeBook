# coding=utf-8

from flask import redirect, flash, url_for, request, abort, send_from_directory
from flask import Blueprint, current_app, session
from forms import PostForm, FindFile, EditInfoForm, EditBasic, EditPassword
from flask_login import login_required, current_user
from app import db
from werkzeug.utils import secure_filename
from models import Category, Favorite, User, Comment, Role, Information
import datetime
from ..email import send_email
import os
from flask import render_template, g
import time
from sqlalchemy import text
import subprocess
import threading
from auth import logout
import cgi
from tornado.ioloop import IOLoop
import re

main = Blueprint("main", __name__)

file_dir = os.getcwd() + "/markdown"

user_page = dict()


def pop(args):
    print str(args[0]) + "has pop!"
    user_page.pop(args[0], None)


def work(_id, info):
    print _id + "begin work"
    name = _id + ".md"
    pdf = _id + ".pdf"
    filename = file_dir + "/" + name
    print filename
    pdf_name = file_dir + "/" + pdf
    _file = open(filename, "wb")
    line_list = info.split("\n")
    pattren = re.compile(r"\|.+\|")
    begin = re.compile(r"\|[-]+\|")

    tmp = ""
    status = False

    for line in line_list:
        if begin.match("".join(line.split())) and tmp:
            status = True
        elif pattren.match(line.strip()) and not status:
            if tmp:
                _file.write(tmp + "\n")
            tmp = line
            continue
        elif status and not pattren.match(line.strip()):
            status = False
        if status:
            if tmp:
                _file.write(cgi.escape(tmp) + "\n")
            _file.write(cgi.escape(line) + "\n")
        else:
            if tmp:
                _file.write(tmp + "\n")
            _file.write(line + "\n")
        tmp = ""

    if tmp:
        _file.write(tmp + "\n")
    _file.close()
    user_page[_id] = 'work'
    IOLoop.instance().add_timeout(50, callback=pop, args=(_id,))
    os.system("pandoc {} --template eisvogel  --pdf-engine xelatex   -o {} -V CJKmainfont='SimSun'  "
              "--highlight-style pygments --listings ".format(filename, pdf_name))


@main.route("/create_doc", methods=['GET', "POST"])
@login_required
def edit():
    form = PostForm()
    p = Category()
    if request.method == "POST":
        p.title = form.title.data
        p.content = form.text.data
        p.user = current_user.id
        p.update_time = datetime.datetime.now()
        db.session.add(p)
        db.session.commit()
        for _user in current_user.followers:
            info = Information()
            info.launch_id = current_user.id
            info.receive_id = _user.follower_id
            db.session.add(info)
            db.session.flush()
            info.info = u"您关注的用户 " + current_user.username + u" 发表了新的文章 " + u"<a style='color: #d82433' " \
                                                                            u"href='{}?check={}'>{}</a>".format(
                u"/display/" + str(p.id), info.id, p.title) + u"。"
        t = threading.Thread(target=work, args=(str(p.id), p.content.encode("utf-8")))
        t.start()
        db.session.commit()

        flash(u'保存成功！', 'success')
        return redirect(url_for('main.edit'))
    return render_template('edit.html', form=form)


@main.route("/", methods=['GET', "POST"])
def index():
    return render_template("index.html")


@main.route("/my_doc/<int:key>/<int:_id>", methods=['GET', "POST"])
def my_doc(key, _id):
    temp = Category.query.filter_by(user=key)
    length = len(temp.all())
    page_num = length / 10 if length % 10 == 0 else length / 10 + 1
    docs = temp.order_by(Category.id.desc()).paginate(_id, 10, error_out=True).items
    # 总数量 文章列表 当前id 总页数
    return render_template("mydoc.html", key=key, length=length, docs=docs, page=_id, page_num=page_num)


@main.route("/display/<key>", methods=['GET', "POST"])
def dispaly(key):
    p = Category.query.filter_by(id=key).first()
    if not current_user.is_anonymous:
        is_collect = Favorite.query.filter_by(favorited_id=key, favorite_id=current_user.id).first()
        if request.args. has_key('check'):
            temp = Information.query.filter_by(id=int(request.args['check'])).first()
            temp.confirm = True
            db.session.add(temp)
            db.session.commit()
            message_nums = len([info for info in current_user.received if info.confirm is False])
            if message_nums > 0:
                g.message_nums = message_nums
            else:
                g.message_nums = None
    else:
        is_collect = None
    if not p:
        flash(u'该文章不存在！', 'warning')
        abort(404)
    comments = Comment.query.filter_by(post_id=key).all()
    print(request.url)
    permission = Role.query.filter_by(id=current_user.role_id).first().permissions

    html = u'''
                    <li class="dropdown">
<a href="#" class="dropdown-toggle" data-toggle="dropdown"> 处理 <b class="caret"></b></a>
                                <ul class="dropdown-menu multi-column columns-3">
                                <li>
                                <div class="col-sm-4">
                                    <ul class="multi-column-dropdown">
                                    {}
                                    </ul>
                                    </div>
                                    <div class="clearfix"></div>
                                </li>
                            </ul>
                            </li>
                            '''

    for _index in range(len(comments)):
        comments[_index].author = User.query.filter_by(id=comments[_index].author_id).first().username
        comments[_index].img = comments[_index].author_id
        if comments[_index].comment_user:
            comments[_index].comment_id = User.query.filter_by(username=comments[_index].comment_user).first().id
        string = ""

        if not current_user.is_authenticated:
            comments[_index].html = ""
            continue

        elif comments[_index].author_id == current_user.id:
            string = u'''
            <li style="cursor: pointer;"><a  onclick="edit_comment({})">修改</a></li>
            <li><a href="/del_comment/{}">删除</a></li>
            <li style="cursor: pointer;"><a  onclick="response_comment('{}')">回复</a></li>
            '''.format(comments[_index].id, comments[_index].id, comments[_index].author)

        elif permission >= 31 or current_user.id == p.user:
            string = u'''<li style="cursor: pointer;"><a  onclick="response_comment('{}')">回复</a></li>
                         <li><a href="/del_comment/{}">删除</a></li>
                        '''.format(comments[_index].author, comments[_index].id)

        else:
            string = u'''<li style="cursor: pointer;"><a onclick="response_comment('{}')">回复</a></li>
                                    '''.format(comments[_index].author)

        comments[_index].html = html.format(string)

    return render_template("display.html", post=p, is_collect=is_collect, comments=comments)


@main.route("/cancel/<key>", methods=['GET', "POST"])
@login_required
def cancel(key):
    p = Category.query.filter_by(id=key).first()
    user = User.query.filter_by(id=p.user).first()
    if not current_user.is_anonymous:
        is_collect = Favorite.query.filter_by(favorited_id=key, favorite_id=current_user.id).first()
    else:
        is_collect = None
    if not p:
        flash(u'该文章不存在！', 'warning')
        abort(404)
    if not is_collect:
        flash(u"您没有收藏该文章,无法取消收藏!", "warning")
        return redirect("/display/" + key)
    else:
        db.session.delete(is_collect)
        p.collect_num -= 1
        user.collect_num -= 1
        db.session.add(p)
        db.session.add(user)
        db.session.commit()
        flash(u"取消收藏成功!", "success")
        return redirect("/display/" + key)


@main.route("/show_collect/", methods=['GET', "POST"])
@login_required
def show_collect():
    collects = Favorite.query.filter_by(favorite_id=current_user.id).all()

    doc_list = list()

    for _collect in collects:
        page = Category.query.filter_by(id=_collect.favorited_id).first()
        page.update_time = Favorite.query.filter_by(favorited_id=_collect.favorited_id).first().update_time
        doc_list.append(page)

    return render_template("collect.html", doc_list=doc_list, length=len(doc_list))


@main.route("/del_file/<int:key>/<int:page>", methods=['GET', "POST"])
@login_required
def del_file(key, page):
    p = Category.query.filter_by(id=key, user=current_user.id).first()
    if not p:
        flash(u'该文章不存在！', 'warning')
        abort(404)
    current_user.collect_num -= p.collect_num
    db.session.add(current_user)
    filename = os.getcwd() + "/markdown/" + str(p.id) + ".pdf"
    if os.path.exists(filename):
        os.system("rm -f {} ".format(filename))
    db.session.delete(p)
    db.session.commit()
    flash(u'删除成功！', 'success')
    return redirect(url_for("main.my_doc", key=current_user.id, _id=page))


"""
pandoc -s --smart --latex-engine=xelatex -V CJKmainfont='SimSun' -V mainfont="SimSun" -V geometry:margin=1in test.md  -o output.pdf
"""


@main.route("/collect/<key>", methods=['GET', 'POST'])
@login_required
def collect(key):
    p = Category.query.filter_by(id=key).first()
    user = User.query.filter_by(id=p.user).first()
    if not p:
        flash(u'该文章不存在！', 'warning')
        abort(404)
    f = Favorite()
    f.favorite_id = current_user.id
    f.update_time = datetime.datetime.now()
    f.favorited_id = key
    p.collect_num += 1
    user.collect_num += 1
    f.update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if Favorite.query.filter_by(favorite_id=current_user.id, favorited_id=key).first():
        flash(u'文章已经收藏！', 'warning')
        return redirect("/display/" + key)

    db.session.add(f)
    db.session.add(p)
    db.session.add(user)
    db.session.commit()
    flash(u'收藏成功！', 'success')
    return redirect("/display/" + key)


@main.route("/edit_file/<int:key>", methods=['GET', "POST"])
@login_required
def edit_file(key):
    p = Category.query.filter_by(id=key, user=current_user.id).first()
    if not p:
        flash(u'该文章不存在！', 'warning')
        abort(404)
    form = PostForm(title=p.title, text=p.content)
    if request.method == "POST":
        p.title = request.values.get("title")
        p.content = request.values.get("text")
        p.update_time = datetime.datetime.now()
        filename = os.getcwd() + "/markdown/" + str(p.id) + ".pdf"
        if os.path.exists(filename):
            os.system("rm -f {} ".format(filename))
        db.session.add(p)
        db.session.commit()
        t = threading.Thread(target=work, args=(str(p.id), p.content.encode("utf-8")))
        t.start()
        flash(u'保存成功！', 'success')
        return redirect(url_for('main.edit'))
    return render_template('edit.html', form=form)


@main.route("/download/<key>", methods=['GET'])
@login_required
def downloader(key):
    p = Category.query.filter_by(id=key, user=current_user.id).first()
    if not p:
        flash(u'该文章不存在！', 'warning')
        abort(404)

    pdf = str(p.id) + ".pdf"
    pdf_name = file_dir + "/" + pdf

    if os.path.exists(pdf_name):
        return send_from_directory(file_dir, pdf, as_attachment=True)

    popen = None
    if not user_page.has_key(str(p.id)):
        user_page[str(p.id)] = 'work'
        print str(p.id) + "begin work"
        info = p.content.encode("utf-8")
        name = str(p.id) + ".md"
        pdf = str(p.id) + ".pdf"
        filename = file_dir + "/" + name
        pdf_name = file_dir + "/" + pdf
        _file = open(filename, "wb")
        line_list = info.split("\n")
        pattren = re.compile(r"\|.+\|")
        begin = re.compile(r"\|[-]+\|")

        tmp = ""
        status = False

        for line in line_list:
            if begin.match("".join(line.split())) and tmp:
                status = True
            elif pattren.match(line.strip()) and not status:
                if tmp:
                    _file.write(tmp + "\n")
                tmp = line
                continue
            elif status and not pattren.match(line.strip()):
                status = False
            if status:
                if tmp:
                    _file.write(cgi.escape(tmp) + "\n")
                _file.write(cgi.escape(line) + "\n")
            else:
                if tmp:
                    _file.write(tmp + "\n")
                _file.write(line + "\n")
            tmp = ""

        if tmp:
            _file.write(tmp + "\n")
        _file.close()

        user_page[str(p.id)] = 'work'

        shell = "pandoc {} --template eisvogel  --pdf-engine xelatex   -o {} -V CJKmainfont='SimSun'  " \
                "--highlight-style pygments --listings ".format(filename, pdf_name)
        import shlex
        popen = subprocess.Popen(shlex.split(shell), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        IOLoop.instance().add_timeout(50, callback=pop, args=(str(p.id),))
    else:
        print "have one working"
    count = 0

    while True:
        if os.path.exists(pdf_name):
            return send_from_directory(file_dir, pdf, as_attachment=True)

        elif count == 50:
            flash(u'导出失败, 请检查您的文档!(例如:图片格式只能使用jpg,png, Latex语法只支持XeLax!)', 'warning')
            IOLoop.instance().add_timeout(0, callback=pop, args=(str(p.id),))
            return redirect(url_for("main.my_doc", key=current_user.id, _id=1))
        else:
            if popen and popen.poll() is None:
                line = popen.stdout.readline()
                line += popen.stderr.readline()
                print line
                if 'Error' in line or 'Warning' in line or "Could not" in line or 'WARNING' in line:
                    popen.terminate()
                    flash(u'导出失败, {}'.format(line), 'warning')
                    IOLoop.instance().add_timeout(0, callback=pop, args=(str(p.id),))
                    return redirect(url_for("main.my_doc", key=current_user.id, _id=1))
            count += 1
            time.sleep(1)


@main.route("/find_file/<int:key>", methods=['GET', 'POST'])  # 七天最高
def find_file(key):
    form = FindFile()
    if key == 7:
        hot_doc_list = Category.query.from_statement(text("SELECT * FROM markdown.category where DATE_SUB(CURDATE(), "
                                                          "INTERVAL 7 DAY) <= date(update_time) ORDER BY collect_num desc,update_time desc  LIMIT 10 ;")).all()
    else:
        hot_doc_list = Category.query.from_statement(text("SELECT * FROM markdown.category ORDER BY "
                                                          "collect_num desc,update_time desc LIMIT 10 ;")).all()
    for doc in hot_doc_list:
        doc.username = User.query.filter_by(id=doc.user).first().username
    if form.validate_on_submit():
        doc_list = Category.query.whoosh_search(form.input.data).all()

        for doc in doc_list:
            doc.username = User.query.filter_by(id=doc.user).first().username
        length = len(doc_list)
        if not doc_list:
            flash(u"没有找到符合要求的文章!", "warning")
            return redirect(url_for("main.find_file", key=7))

        return render_template("find_file.html", form=form, doc_list=doc_list, length=length, key=7)
    return render_template("find_file.html", form=form, hot_doc_list=hot_doc_list, key=key)


@main.route("/edit_email", methods=['GET', 'POST'])
@login_required
def edit_email():
    form = EditInfoForm()

    if request.method == "POST":

        # filter 支持表达式 比 filter 更强大

        if User.query.filter_by(email=form.email.data).first() and current_user.email != form.email.data:
            flash(u"该邮箱已经被注册过，请重新输入!", "warning")
            return redirect(url_for("main.edit_info"))

        current_user.email = form.email.data
        current_user.confirmed = False
        db.session.add(current_user)
        db.session.commit()

        token = current_user.generate_confirmation_token()
        send_email([current_user.email], u'验证您的账号',
                   'auth/email/confirm', user=current_user, token=token)

        flash(u"一封验证邮件发送到了你的邮箱,请您验收!", "success")

        logout()
        return redirect(url_for("auth.login"))

    return render_template("edit/edit_email.html", form=form)


@main.route("/edit_basic", methods=['GET', 'POST'])
@login_required
def edit_basic():
    form = EditBasic()
    form.user_type.data = ["Moderator", "Administrator", "User"][current_user.role_id - 1]
    if request.method == "POST":
        # filter 支持表达式 比 filter 更强大

        if User.query.filter_by(username=form.username.data).first() and current_user.username != form.username.data:
            flash(u"该用户名已经被注册过，请重新输入!", "warning")
            return redirect(url_for("main.edit_basic"))

        _file = request.files['filename'] if request.files.has_key("filename") else None
        if _file:
            _type = _file.filename.split(".")[-1].lower()

            if not _type or _type not in ['jpeg', 'jpg', 'bmp', "png"]:
                flash(u"图片格式错误，当前只支持'jpeg', 'jpg', 'bmp', 'png'!", "warning")
                return redirect(url_for("main.edit_basic"))

            dirname = current_app.config['UPLOAD_FOLDER']  # 截图存放地点
            current_user.image_name = secure_filename(str(current_user.id) + "." + _type)
            if not os.path.exists(dirname):
                try:
                    os.makedirs(dirname)
                    _file.save(os.path.join(dirname, current_user.image_name))
                except Exception as e:
                    print e
            else:
                _file.save(os.path.join(dirname, current_user.image_name))

        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()

        flash(u"修改成功!", "success")
        return redirect(url_for("main.index"))

    return render_template("edit/edit_basic.html", form=form)


@main.route("/edit_password", methods=['GET', 'POST'])
@login_required
def edit_password():
    form = EditPassword()

    if request.method == "POST":
        if session.get('check') != 'true' and not current_user.verify_password(form.old.data):
            flash(u"用户密码错误，请重新输入!", "warning")
            return redirect(url_for("main.edit_password"))

        current_user.password = form.password.data
        session['check'] = 'false'
        db.session.add(current_user)
        db.session.commit()

        flash(u"修改成功!", "success")
        return redirect(url_for("main.index"))

    return render_template("edit/edit_password.html", form=form)


@main.route("/add_comment/<key>", methods=["POST"])
@login_required
def add_comment(key):
    if request.method == "POST":
        info = request.form["comment"]
        if not Category.query.filter_by(id=key).first():
            abort(404)
        comment = Comment(body=cgi.escape(info), author_id=current_user.id, post_id=key)
        comment.timestamp = datetime.datetime.now()
        _info = Information()
        _info.time = datetime.datetime.now()
        _info.launch_id = current_user.id
        category = Category.query.filter_by(id=key).first()
        _info.receive_id = category.user
        _info.info = u"用户" + current_user.username + u" 对您的文章" + u"<a style='color: #d82433' " \
                                                                 u"href='{}'>{}</a>".format(
            u"/display/" + str(category.id), category.title) + u"进行了评论!"
        db.session.add(_info)
        db.session.add(comment)
        db.session.commit()
        flash(u"添加成功!", "success")
        return redirect("/display/" + key)


@main.route("/edit_comment/<key>", methods=["POST"])
@login_required
def edit_comment(key):
    if request.method == "POST":
        info = request.form["comment"]
        comment = Comment.query.filter_by(id=key).first()
        if not comment:
            abort(404)
        comment.body = info
        _info = Information()
        _info.time = datetime.datetime.now()
        _info.launch_id = current_user.id
        category = Category.query.filter_by(id=comment.post_id).first()
        _info.receive_id = category.user
        _info.info = u"用户" + current_user.username + u" 对您的文章" + u"<a style='color: #d82433' " \
                                                                 u"href='{}'>{}</a>".format(
            u"/display/" + str(category.id), category.title) + u"修改了评论!"
        db.session.add(_info)
        comment.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.session.add(comment)
        db.session.commit()
        flash(u"修改成功!", "success")
        return redirect("/display/" + str(comment.post_id))


@main.route("/response_comment/<int:post_id>/<key>", methods=["POST"])
@login_required
def response_comment(post_id, key):
    if request.method == "POST":
        info = request.form["comment"]
        if not Category.query.filter_by(id=post_id).first():
            abort(404)
        comment = Comment(body=cgi.escape(info), author_id=current_user.id, post_id=post_id)
        comment.comment_user = User.query.filter_by(username=key).first()
        if not comment.comment_user:
            abort(404)
        _info = Information()
        _info.time = datetime.datetime.now()
        _info.launch_id = current_user.id
        category = Category.query.filter_by(id=post_id).first()
        _info.receive_id = comment.comment_user.id
        comment.comment_user = comment.comment_user.username
        comment.timestamp = datetime.datetime.now()
        _info.info = u"用户" + current_user.username + u" 对您在" + u"<a style='color: #d82433' " \
                                                               u"href='{}'>{}</a>".format(
            u"/display/" + str(category.id), category.title) + u"的评论进行了回复!"
        db.session.add(_info)
        db.session.add(comment)
        db.session.commit()
        flash(u"回复成功!", "success")
        return redirect("/display/" + str(post_id))


@main.route("/del_comment/<key>", methods=['GET', 'POST'])
@login_required
def del_comment(key):
    comment = Comment.query.filter_by(id=key).first()
    if not comment:
        abort(404)

    category = Category.query.filter_by(id=comment.post_id).first()  # 文章

    # 若是管理员，文章作者，评论作者都能删除评论

    if current_user.role >= 31 or current_user.id == comment.author_id or current_user.id == category.user:
        db.session.delete(comment)
        db.session.commit()
        flash(u"删除成功!", "success")
        return redirect("/display/" + str(category.id))

    else:
        flash(u"您无权删除该条评论!", "warning")
        return redirect("/display/" + str(category.id))


# @main.route("/disable_comment/<key>", methods=['POST'])
# @login_required
# def disable_comment(key):
#     comment = Comment.query.filter_by(id=key).first()
#     if not comment:
#         abort(404)
#
#     category = Category.query.filter_by(id=comment.post_id).first()  # 文章
#
#     # 管理员和作者可以屏蔽评论
#
#     if current_user.role >= 31 or current_user.id == category.user:
#         comment.disabled = True
#         db.session.add(comment)
#         db.session.commit()
#         flash(u"屏蔽成功!", "success")
#         return redirect(url_for("/display/" + category.id))
#     else:
#         flash(u"您无权屏蔽该条评论!", "warning")
#         return redirect(url_for("/display/" + category.id))


@main.route("/show_image/<key>", methods=['GET', 'POST'])
def show_image(key):
    user = User.query.filter_by(id=key).first()
    if not user:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], "-1.jpg")
    else:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], user.image_name)
