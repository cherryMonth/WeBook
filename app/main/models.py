# coding = utf-8

from app import db
import datetime


class Category(db.Model):

    __tablename__ = "category"
    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    title = db.Column(db.String(30), nullable=False)
    content = db.Column(db.Text(10000), nullable=False)
    html = db.Column(db.Text(50000), nullable=False)
    update_time = db.Column(db.DateTime, default=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), nullable=True)
