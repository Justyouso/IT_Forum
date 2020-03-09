# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-2 上午9:15

from flask import Blueprint
from flask_restful import Api
from app.article.views import ArticleCreate,ArticleList

article = Blueprint("article", __name__)
_api = Api(article)

_api.add_resource(ArticleCreate, "/create")
_api.add_resource(ArticleList, "/list")
