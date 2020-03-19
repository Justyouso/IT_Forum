# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-2 上午9:15
from flask_restful import Resource, reqparse,marshal
from app.models import Article
from app.article.serializers import ArticleListSerializer, \
    ArticleDetailSerializer
from app import db
from sqlalchemy import and_,not_,desc,asc
from app.utlis.tools import generate_words


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
        self.parser.add_argument("per_page", type=int, default=10, help="每页数量")
        self.parser.add_argument("author", type=str, default="", trim=True,
                                 help="作者ID")
        self.parser.add_argument("keywords", type=str, default="", trim=True,
                                 help="关键词")
        self.parser.add_argument("order", type=str, default="timestamp",
                                 trim=True, help="排序字段")
        self.parser.add_argument("sort", type=str, default="desc",
                                 choices=["desc", "asc"],
                                 trim=True, help="排序方式")

    def get(self):
        args = self.parser.parse_args()

        # 组装查询参数
        params = and_()
        if args["author"]:
            params = and_(params, Article.author_id == args["author"])
        if args["keywords"]:
            params = and_(params,
                          Article.body.like("%" + args["keywords"] + "%"))
        sort = desc(args["order"]) if args["sort"] == "desc" else asc(
            args["order"])

        articles = Article.query.filter(params).order_by(sort).paginate(
            args["page"], per_page=args["per_page"], error_out=False
        )
        # 指定返回字段
        fields = ["id", "title", "summary", "read", "author", "author_id",
                  "comments"]
        serialize = {k: v for k, v in ArticleListSerializer.items() if
                     k in fields}
        data = [marshal(item, serialize) for item in articles.items]

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


class ArticleWordCloud(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("page", type=int, default=1, help="页数")
        self.parser.add_argument("per_page", type=int, default=10, help="每页数量")
        self.parser.add_argument("articles",type=str, default="", trim=True,
                                 help="文章ID，使用逗号隔开")
        self.parser.add_argument("author", type=str, default="", trim=True,
                                 help="作者ID")
        self.parser.add_argument("keywords", type=str, default="", trim=True,
                                 help="关键词")

    def get(self):
        args = self.parser.parse_args()

        # 组装查询参数
        params = and_()
        if args["author"]:
            params = and_(params, Article.author_id == args["author"])
        if args["keywords"]:
            params = and_(params,
                          Article.body.like("%" + args["keywords"] + "%"))
        if args["articles"]:
            article_ids = [args["articles"].split(",")]
            params = and_(params, Article.id.in_(article_ids))

        articles = Article.query.filter(params).order_by(
            Article.timestamp.desc()).paginate(
            args["page"], per_page=args["per_page"], error_out=False
        )

        data = generate_words([i.body for i in articles.items])
        return {"data": data, "message": "", "resCode": 0}