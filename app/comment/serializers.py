# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-9 下午5:57
from flask_restful import fields
from app.utlis.formatters import AuthorFormatter, CountFormatter,BodyNumFormatter

CommentListSerializer = {
    "id": fields.String(default=""),
    "body": fields.String(default=""),
    "author_id": fields.String(default=""),
    "author": AuthorFormatter(default=""),
    "article_id": fields.String(default=""),
    "disabled": fields.Boolean(default=True),
    "body_html": fields.String(default=""),
    "timestamp":fields.String(default="")
}

ArticleDetailSerializer = {
    "id": fields.String(default=""),
    "title": fields.String(default=""),
    "summary": fields.String(default=""),
    "body_num": BodyNumFormatter(default=0),
    "body_md": fields.String(default=""),
    "body_html": fields.String(default=""),
    "author_id": fields.Integer,
    "author": AuthorFormatter(default=""),
    "read": fields.Integer(default=0),
    "comments": CountFormatter(default=0)
}