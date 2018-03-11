# coding=utf-8
from wtforms import StringField, TextAreaField, SelectMultipleField, SubmitField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length
from models import Category


class PostForm(FlaskForm):
    title = StringField("", render_kw={'placeholder': u'主题(仅限于30字内...)'})
    text = TextAreaField("", [DataRequired(), Length(max=10000)])
    categories = SelectMultipleField('Categories', coerce=int)
    submit = SubmitField(u"发布文章")

    def __init__(self):
        super(PostForm, self).__init__()
        self.categories.choices = [(c.id, c.title) for c in Category.query.order_by('id')]
