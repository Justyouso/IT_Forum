# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-9 下午5:57
from flask_restful import fields
from app.utlis.formatters import AuthorFormatter,CommentsFormatter

ArticleListSerializer = {
    "id": fields.String(default=""),
    "title": fields.String(default=""),
    "body_md": fields.String(default=""),
    "body_html": fields.String(default=""),
    "author_id": fields.Integer,
    "author": AuthorFormatter(default=""),
    "read": fields.Integer(default=0),
    "comments": CommentsFormatter(default=0)
}
