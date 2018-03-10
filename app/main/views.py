# coding=utf-8

from flask import render_template, redirect, flash, url_for, request
from flask import Blueprint
from forms import PostForm
from app import db
from models import Category
import datetime
from config import config

main = Blueprint("main", __name__)


@main.route("/create_doc", methods=['GET', "POST"])
def edit():
    form = PostForm()
    p = Category()
    if request.method == "POST":
        p.title = form.title.data
        p.content = form.text.data
        p.html = config['html']
        if not p.content:
            flash(u'您没有创建有效的文档内容，无法保存！', 'warning')
            return redirect(url_for('main.edit'))
        p.update_time = datetime.datetime.now()
        db.session.add(p)
        db.session.commit()
        flash(u'保存成功！', 'success')
        return redirect(url_for('main.edit'))

    form.title.data = p.title
    form.text.data = p.content
    return render_template('edit.html', form=form, post=p)


@main.route("/", methods=['GET', "POST"])
def index():
    return render_template("index.html")


@main.route("/get_html", methods=['GET', 'POST'])
def get_html():
    config['html'] = request.values.get("html")
    return "OK"


@main.route("/my_doc", methods=['GET', "POST"])
def my_doc():
    docs = Category.query.filter(Category.id > 0).all()
    length = len(docs)
    return render_template("mydoc.html", length=length, docs=docs)


@main.route("/display/<title>", methods=['GET', "POST"])
def dispaly(title):
    p = Category.query.filter_by(title=title).first()
    return render_template("display.html",  post=p)
