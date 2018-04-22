# coding=utf-8

from flask import render_template, redirect, flash, url_for, request
from flask import Blueprint
from forms import PostForm
from app import db
from models import Category
import datetime
from config import config

user = Blueprint("user", __name__)
