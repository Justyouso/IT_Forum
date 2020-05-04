# -*- coding: utf-8 -*-
# @Author: dmq
# @Time: 20-3-2 上午9:15
from flask_restful import Resource, reqparse, marshal
from sqlalchemy import and_, desc, asc

from app import db
from app.article.serializers import ArticleListSerializer, \
    ArticleDetailSerializer
from app.exts import es_client
from app.models import Article, User
from app.utlis.tools import build_es_query_params
from app.utlis.tools import generate_words
from config import config_module


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
    """文章详情"""

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("author", type=str, help="用户ID")

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

    def delete(self, id):
        args = self.parser.parse_args()
        article = Article.query.filter_by(id=id,
                                          author_id=args["author"]).first()
        if article:
            try:
                db.session.delete(article)
                db.session.commit()
                es_client.delete(index=config_module.ES_SETTING["index"],
                                 doc_type=config_module.ES_SETTING["doc_type"],
                                 id=id)
                data = {"data":"","message": "", "resCode": 0}
            except Exception as ex:
                print(ex)
                data = {"data":"","message": "删除失败", "resCode": 1}

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
        if args["articles"]:
            article_ids = [args["articles"].split(",")]
            params = and_(params, Article.id.in_(article_ids))

        sort = desc(args["order"]) if args["sort"] == "desc" else asc(
            args["order"])

        articles = Article.query.filter(params).order_by(sort).paginate(
            args["page"], per_page=args["per_page"], error_out=False
        )

        data = generate_words([i.body for i in articles.items])
        return {"data": data, "message": "", "resCode": 0}


class ArticleUpdate(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("body_md", type=str, required=True, default="",
                                 help="文章markdown")
        self.parser.add_argument("body_html", type=str, required=True,
                                 default="", help="文章html")

    def put(self,id):
        args = self.parser.parse_args()
        result = Article.update(id, args["body_html"], args["body_md"])
        if result:
            data = {"data": "", "message": "编辑成功", "resCode": 0}
        else:
            data = {"data": "", "message": "编辑失败", "resCode": 1}
        return data


class ArticleHotList(Resource):
    """
    文章推荐,通过user获得topic,再将topic在es中进行短语匹配
    """
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("page", type=int, default=1, help="页数")
        self.parser.add_argument("per_page", type=int, default=10, help="每页数量")
        self.parser.add_argument("author", type=str, default="8", trim=True,
                                 help="作者ID")
        self.parser.add_argument("keywords", type=str, default="", trim=True,
                                 help="关键词")

    def get(self):
        args = self.parser.parse_args()
        user = User.query.filter_by(id=args["author"]).first()

        # 构建es匹配参数
        es_query_params = {
            "topic": user.topic,
            "keywords": args["keywords"],
            "skip": (args["page"] - 1) * args["per_page"],
            "size": args["per_page"]
        }

        # 构建es匹配语句
        search = build_es_query_params(**es_query_params)
        # 查询es
        resp = search.execute()
        # 获取匹配的文章ids
        article_ids = [i["_id"] for i in resp.hits.hits]
        # 使用es查询出的文章id,取出相应文章数据
        articles = Article.query.filter(Article.id.in_(article_ids)).all()
        # 指定返回字段
        fields = ["id", "title", "summary", "read", "author", "author_id",
                  "comments"]
        serialize = {k: v for k, v in ArticleListSerializer.items() if
                     k in fields}
        result = [marshal(item, serialize) for item in articles]
        # 根据article_ids的顺序进行排序
        result_dict = {i["id"]: i for i in result}
        data = [result_dict.get(id) for id in article_ids]
        return {"data": data, "message": "", "resCode": 0}


class ArticleHotWordCloud(Resource):
    """
    通过user获得topic,再将topic在es中进行短语匹配,查询出文章再生成词云
    """

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("page", type=int, default=1, help="页数")
        self.parser.add_argument("per_page", type=int, default=10, help="每页数量")
        self.parser.add_argument("author", type=str, default="8", trim=True,
                                 help="作者ID")
        self.parser.add_argument("keywords", type=str, default="", trim=True,
                                 help="关键词")

    def get(self):
        args = self.parser.parse_args()
        user = User.query.filter_by(id=args["author"]).first()

        # 构建es匹配参数
        es_query_params = {
            "topic": user.topic,
            "keywords": args["keywords"],
            "skip": (args["page"] - 1) * args["per_page"],
            "size": args["per_page"]
        }

        # 构建es匹配语句
        search = build_es_query_params(**es_query_params)
        # 查询es
        resp = search.execute()
        # 获取匹配的文章ids
        article_ids = [i["_id"] for i in resp.hits.hits]
        # 使用es查询出的文章id,取出相应文章数据
        articles = Article.query.filter(Article.id.in_(article_ids)).all()

        # 生成词云
        data = generate_words([i.body for i in articles])
        return {"data": data, "message": "", "resCode": 0}


class ArticleSearchList(Resource):
    """
    文章搜索,通过获取关键词在es中进行短语匹配
    """

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("page", type=int, default=1, help="页数")
        self.parser.add_argument("per_page", type=int, default=10, help="每页数量")
        self.parser.add_argument("keywords", type=str, default="", trim=True,
                                 help="关键词")

    def get(self):
        args = self.parser.parse_args()

        # 构建es匹配参数
        es_query_params = {
            "keywords": args["keywords"],
            "skip": (args["page"] - 1) * args["per_page"],
            "size": args["per_page"]
        }

        # 构建es匹配语句
        search = build_es_query_params(**es_query_params)
        # 查询es
        resp = search.execute()
        # 获取匹配的文章ids
        article_ids = [i["_id"] for i in resp.hits.hits]
        # 使用es查询出的文章id,取出相应文章数据
        articles = Article.query.filter(Article.id.in_(article_ids)).all()
        # 指定返回字段
        fields = ["id", "title", "summary", "read", "author", "author_id",
                  "comments"]
        serialize = {k: v for k, v in ArticleListSerializer.items() if
                     k in fields}
        result = [marshal(item, serialize) for item in articles]
        # 根据article_ids的顺序进行排序
        result_dict = {i["id"]: i for i in result}
        data = [result_dict.get(id) for id in article_ids]

        return {"data": data, "total": resp.hits.total, "message": "",
                "resCode": 0}


class TestService(Resource):
    def get(self):
        return "服务正常"
