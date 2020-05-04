# -*- coding: utf-8 -*-
# @Author: dmq
# @Time: 20-3-2 上午9:15

from flask import Blueprint
from flask_restful import Api
from app.article.views import ArticleCreate, ArticleNewList, ArticleDetail, \
    ArticleWordCloud, ArticleUpdate, ArticleHotList, ArticleHotWordCloud, \
    ArticleSearchList, TestService

article = Blueprint("article", __name__)
_api = Api(article)

_api.add_resource(ArticleCreate, "/create")
_api.add_resource(ArticleNewList, "/new/list")
_api.add_resource(ArticleDetail, "/<int:id>")
_api.add_resource(ArticleUpdate, "/<int:id>")
_api.add_resource(ArticleWordCloud, "/wordcloud")

_api.add_resource(ArticleHotList, "/hot/list")
_api.add_resource(ArticleHotWordCloud, "/hot/wordcloud")
_api.add_resource(ArticleSearchList, "/search")
_api.add_resource(TestService, "/test")
