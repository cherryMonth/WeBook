# coding=utf-8
from wtforms import StringField, TextAreaField, SelectMultipleField, SubmitField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length
from models import Category


class PostForm(FlaskForm):
    title = StringField('', render_kw={'placeholder': u'主题'}, validators=[DataRequired(), Length(max=20)])
    text = TextAreaField(u'正文', [DataRequired(), Length(max=1000)])
    categories = SelectMultipleField('Categories', coerce=int)
    submit = SubmitField(u"提交")

    def __init__(self):
        super(PostForm, self).__init__()
        self.categories.choices = [(c.id, c.title) for c in Category.query.order_by('id')]
