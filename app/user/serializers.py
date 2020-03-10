# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-9 下午5:57
from flask_restful import fields
from app.utlis.formatters import AuthorFormatter, CountFormatter

UserListSerializer = {
    "id": fields.String(default=""),
    "email": fields.String(default=""),
    "username": fields.String(default=""),
    "article": CountFormatter(default=0),
    "followed": CountFormatter(default=0)
}
