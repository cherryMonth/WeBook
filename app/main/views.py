# coding=utf-8

from flask import render_template, redirect, flash, url_for, request
from flask import Blueprint
from forms import PostForm
from app import db
from models import Category
import datetime
from config import config

main = Blueprint("main", __name__)


@main.route("/", methods=['GET', "POST"])
def index():
    form = PostForm()
    p = Category()
    if form.validate_on_submit():
        p.title = form.title.data
        p.content = form.text.data
        p.html = config['html']
        p.update_time = datetime.datetime.now()
        db.session.add(p)
        db.session.commit()
        flash(u'保存成功！', 'success')
        return redirect(url_for('main.index'))

    form.title.data = p.title
    form.text.data = p.content
    return render_template('test.html', form=form, post=p)


@main.route("/get_html", methods=['GET', 'POST'])
def get_html():
    config['html'] = request.args.get('html', '0', type=str)
    return "OK"


@main.route("/display/<title>", methods=['GET', "POST"])
def dispaly(title):
    p = Category.query.filter_by(title=title).first()
    return render_template("display.html", post=p.html)
