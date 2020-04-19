# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-2 上午9:15
from flask_restful import Resource, reqparse, marshal
from sqlalchemy import and_, desc, asc

from app import db
from app.comment.serializers import CommentListSerializer
from app.models import Comment


class CommentCreate(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("body", type=str, default="", required=True,
                                 help="文章markdown")
        self.parser.add_argument("user", type=str, required=True,
                                 help="用户id")
        self.parser.add_argument("article", type=str, required=True,
                                 help="文章id")

    def post(self):
        args = self.parser.parse_args()
        try:
            comment = Comment(author_id=args["user"],
                              article_id=args["article"],
                              body=args["body"])
            db.session.add(comment)
            db.session.commit()
            data = {"data": "", "message": "评论成功", "resCode": 0}
        except Exception as ex:
            data = {"data": "", "message": "评论失败", "resCode": 1}
        return data


class CommentList(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("page", type=int, default=1, help="页数")
        self.parser.add_argument("per_page", type=int, default=10, help="每页数量")
        self.parser.add_argument("article", type=str, default="", trim=True,
                                 help="文章ID")
        self.parser.add_argument("disabled", type=bool, default=True,
                                 choices=[True, False], help="是否展示")
        self.parser.add_argument("order", type=str, default="timestamp",
                                 trim=True, help="排序字段")
        self.parser.add_argument("sort", type=str, default="desc",
                                 choices=["desc", "asc"],
                                 trim=True, help="排序方式")

    def get(self):
        args = self.parser.parse_args()

        # 组装查询参数
        params = and_()
        if args["article"]:
            params = and_(params, Comment.article_id == args["article"])
        # 查询是否可见
        params = and_(params, Comment.disabled == args["disabled"])
        sort = desc(args["order"]) if args["sort"] == "desc" else asc(
            args["order"])

        comment = Comment.query.filter(params).order_by(sort).paginate(
            args["page"], per_page=args["per_page"], error_out=False
        )
        # 指定返回字段
        fields = ["id", "body", "author_id", "author", "article_id",
                  "timestamp"]
        serialize = {k: v for k, v in CommentListSerializer.items() if
                     k in fields}
        data = [marshal(item, serialize) for item in comment.items]

        return {"data": data, "total": comment.total, "message": "",
                "resCode": 0}


class CommentDetail(Resource):
    """评论详情"""

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("author", type=str, help="用户ID")

    def delete(self, id):
        args = self.parser.parse_args()
        # 用户自己删除评论
        comment = Comment.query.filter_by(id=id,
                                          author_id=args["author"]).first()

        if not comment:
            comment_tmp = Comment.query.filter_by(id=id).first()
            if comment_tmp.author.id == args["author"]:
                comment = comment_tmp
            elif comment_tmp.author.role.permissions > 7:
                comment = comment_tmp
            else:
                comment = None
        if comment:
            try:
                db.session.delete(comment)
                db.session.commit()
                data = {"data": "", "message": "", "resCode": 0}
            except Exception as ex:
                print(ex)
                data = {"data": "", "message": "删除失败", "resCode": 1}
        else:
            data = {"data": "", "message": "评论不存在", "resCode": 1}

        return data
