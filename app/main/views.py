# coding=utf-8

from flask import render_template, redirect, flash, url_for, request, abort, send_from_directory
from flask import Blueprint
from forms import PostForm, FindFile, EditInfoForm
from flask_login import login_required, current_user
from app import db
from models import Category, Favorite, User, Comment, Role
import datetime
import time
from ..email import send_email
import os
from werkzeug.security import generate_password_hash
import threading
from auth import logout

main = Blueprint("main", __name__)


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
        flash(u'保存成功！', 'success')
        return redirect(url_for('main.edit'))
    return render_template('edit.html', form=form)


@main.route("/", methods=['GET', "POST"])
def index():
    return render_template("index.html")


@main.route("/my_doc", methods=['GET', "POST"])
@login_required
def my_doc():
    docs = Category.query.filter_by(user=current_user.id).all()
    length = len(docs)
    return render_template("mydoc.html", length=length, docs=docs)


@main.route("/display/<key>", methods=['GET', "POST"])
def dispaly(key):
    p = Category.query.filter_by(id=key).first()
    if not current_user.is_anonymous:
        is_collect = Favorite.query.filter_by(favorited_id=key, favorite_id=current_user.id).first()
    else:
        is_collect = None
    if not p:
        flash(u'该文章不存在！', 'warning')
        abort(404)
    comments = Comment.query.filter_by(post_id=key).all()

    permission = current_user.role

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

        if current_user.is_anonymous:
            comments[_index].html = ""

        elif (permission >= 31 or current_user.id == p.user) and comments[_index].author_id == current_user.id:
            string = u'''
            <li><a onclick="edit_comment({})">修改</a></li>
            <li><a href="/del_comment/{}">删除</a></li>
            '''.format(comments[_index].id, comments[_index].id)
            comments[_index].html = html.format(string)
        elif permission >= 31 or current_user.id == p.user or comments[_index].author_id == current_user.id:
            string = u'''
                         <li><a href="/del_comment/{}">删除</a></li>
                        '''.format(comments[_index].id)
            comments[_index].html = html.format(string)

        else:  # 普通用户无权限操作
            comments[_index].html = ""

    return render_template("display.html",  post=p, is_collect=is_collect, comments=comments)


@main.route("/cancel/<key>", methods=['GET', "POST"])
@login_required
def cancel(key):
    p = Category.query.filter_by(id=key).first()
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
    length = len(doc_list)

    return render_template("collect.html", doc_list=doc_list, length=length)


@main.route("/del_file/<key>", methods=['GET', "POST"])
@login_required
def del_file(key):
    p = Category.query.filter_by(id=key, user=current_user.id).first()
    if not p:
        flash(u'该文章不存在！', 'warning')
        abort(404)
    db.session.delete(p)
    db.session.commit()
    flash(u'删除成功！', 'success')
    return redirect(url_for("main.my_doc"))

'''
pandoc -s --smart --latex-engine=xelatex -V CJKmainfont='SimSun' -V mainfont="SimSun" -V geometry:margin=1in test.md  -o output.pdf
'''


@main.route("/collect/<key>", methods=['GET', 'POST'])
@login_required
def collect(key):
    p = Category.query.filter_by(id=key, user=current_user.id).first()
    if not p:
        flash(u'该文章不存在！', 'warning')
        abort(404)
    f = Favorite()
    f.favorite_id = current_user.id
    f.favorited_id = key
    f.update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if Favorite.query.filter_by(favorite_id=current_user.id, favorited_id=key).first():
        flash(u'文章已经收藏！', 'warning')
        return redirect("/display/" + key)

    db.session.add(f)
    db.session.commit()
    flash(u'收藏成功！', 'success')
    return redirect("/display/" + key)


@main.route("/edit_file/<key>", methods=['GET', "POST"])
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
        db.session.add(p)
        db.session.commit()
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

    name = generate_password_hash(key)[20:25] + ".md"
    pdf = name[:-3] + ".pdf"
    file_dir = os.getcwd() + "/markdown"
    filename = file_dir + "/" + name
    pdf_name = file_dir + "/" + pdf
    info = p.content.encode("utf-8")
    import cgi
    import re
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

    # pandoc test.md --template eisvogel --pdf-engine xelatex -o e.pdf -V CJKmainfont='SimSun' -N --highlight-style pygments --listings

    def work():
        os.system("pandoc {} --template eisvogel  --pdf-engine xelatex   -o {} -V CJKmainfont='SimSun'  --highlight-style pygments --listings ".format(filename, pdf_name))

    t = threading.Thread(target=work, args=())
    t.start()
    # os.system("rm -f " + filename)
    count = 0
    while True:
        if os.path.exists(pdf_name):
            return send_from_directory(file_dir, pdf, as_attachment=True)
        elif count == 20:
            flash(u'导出失败, 请检查您的文档!(例如:图片格式只能使用jpg,png, Latex语法只支持XeLax!)', 'warning')
            return redirect(url_for("main.my_doc"))
        else:
            count += 1
            time.sleep(1)


@main.route("/find_file", methods=['GET', 'POST'])
def find_file():
    form = FindFile()
    if form.validate_on_submit():
        doc_list = Category.query.whoosh_search(form.input.data).all()
        length = len(doc_list)
        if not doc_list:
            flash(u"没有找到符合要求的文章!", "warning")
            return redirect(url_for("main.find_file"))
        return render_template("find_file.html", form=form, doc_list=doc_list, length=length)
    return render_template("find_file.html", form=form)


@main.route("/edit_info", methods=['GET', 'POST'])
@login_required
def edit_info():
    form = EditInfoForm()

    if request.method == "POST":

        # filter 支持表达式 比 filter 更强大

        if User.query.filter_by(email=form.email.data).first() and current_user.email != form.email.data:
            flash(u"该邮箱已经被注册过，请重新输入!", "warning")
            return redirect(url_for("main.edit_info"))

        if User.query.filter_by(username=form.username.data).first() and current_user.username != form.username.data:
            flash(u"该用户名已经被注册过，请重新输入!", "warning")
            return redirect(url_for("main.edit_info"))

        current_user.password = form.password.data
        current_user.username = form.username.data
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

    return render_template("edit_info.html", form=form)


@main.route("/add_comment/<key>", methods=["POST"])
def add_comment(key):
    if request.method == "POST":
        if current_user.is_anonymous:
            flash(u"您尚未登录无法评论", "warning")
            return redirect("/display/" + key)

        info = request.form["comment"]
        if not Category.query.filter_by(id=key).first():
            abort(404)
        comment = Comment(body=info, author_id=current_user.id, post_id=key)
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
        comment.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.session.add(comment)
        db.session.commit()
        flash(u"修改成功!", "success")
        return redirect("/display/" + str(comment.post_id))


@main.route("/del_comment/<key>", methods=['GET', 'POST'])
@login_required
def del_comment(key):
    comment = Comment.query.filter_by(id=key).first()
    if not comment:
        abort(404)

    category = Category.query.filter_by(id=comment.post_id).first()   # 文章

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

