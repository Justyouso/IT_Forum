# -*- coding: utf-8 -*-
# @Author: dmq
# @Time: 20-3-2 上午9:15

from flask import Blueprint
from flask_restful import Api
from app.comment.views import CommentCreate, CommentList, CommentDetail

comment = Blueprint("comment", __name__)
_api = Api(comment)

_api.add_resource(CommentCreate, "/create")
_api.add_resource(CommentList, "/list")
_api.add_resource(CommentDetail, "/<string:id>")
