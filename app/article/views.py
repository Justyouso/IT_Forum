# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-2 上午9:15
from flask_restful import Resource, reqparse
from app.models import Article


class ArticleCreate(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("body_md", type=str, default="",
                                 help="文章markdown")
        self.parser.add_argument("body_html", type=str, default="",
                                 help="文章html")
        self.parser.add_argument("author_id", type=int, required=True,
                                 help="用户id")

    def post(self):
        args = self.parser.parse_args()
        result = Article.create(**args)
        if result:
            data = {"data": "", "message": "添加成功", "resCode": 0}
        else:
            data = {"data": "", "message": "添加失败", "resCode": 1}
        return data
