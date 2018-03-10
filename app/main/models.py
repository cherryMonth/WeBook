# coding = utf-8

from app import db
import datetime


class Category(db.Model):

    __tablename__ = "category"
    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    title = db.Column(db.String(20), nullable=False, unique=True)
    content = db.Column(db.Text(1000), nullable=False)
    html = db.Column(db.Text(2000), nullable=False)
    update_time = db.Column(db.DateTime, default=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), nullable=True)
