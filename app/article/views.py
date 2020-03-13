# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-2 上午9:15
from flask_restful import Resource, reqparse,marshal
from app.models import Article
from app.article.serializers import ArticleListSerializer, \
    ArticleDetailSerializer
from app import db
from sqlalchemy import and_


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


class ArticleNewList(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("page", type=int, default=1, help="页数")
        self.parser.add_argument("pre_page", type=int, default=10, help="每页数量")
        self.parser.add_argument("author", type=str, default="", trim=True,
                                 help="作者ID")
        self.parser.add_argument("keywords", type=str, default="", trim=True,
                                 help="关键词")

    def get(self):
        args = self.parser.parse_args()

        # 组装查询参数

        params = and_(
            Article.author_id == args["author"]
            if args["author"] is not None else "",
            Article.body.like("%" + args["keywords"] + "%")
            if args["keywords"] is not None else ""

        )
        articles = Article.query.filter(params).order_by(
            Article.timestamp.desc()).paginate(
            args["page"], per_page=args["pre_page"], error_out=False
        )
        data = [marshal(item, ArticleListSerializer) for item in articles.items]

        return {"data": data, "message": "", "resCode": 0}


class ArticleDetail(Resource):
    def get(self, id):
        article = Article.query.filter_by(id=id).first()
        if article:
            try:
                article.read += 1
                db.session.commit()
            except Exception as ex:
                print(ex)
            data = {"data": marshal(article, ArticleDetailSerializer),
                    "message": "", "resCode": 0}
        else:
            data = {"data": "", "message": "文章不存在", "resCode": 1}
        return data
