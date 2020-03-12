# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-2 上午9:15
from flask_restful import Resource, reqparse, marshal
from app.models import User
from app import db
from app.email import send_mail
from app.utlis.tools import generate_code, set_redis_cache, get_redis_cahe
from sqlalchemy import or_, not_
from app.user.serializers import UserListSerializer


class UserNewList(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("page", type=int, default=1, help="页数")
        self.parser.add_argument("pre_page", type=int, default=10, help="每页数量")
        self.parser.add_argument("user", type=str, default='', help="用户ID")

    def get(self):
        args = self.parser.parse_args()
        if args['user']:
            user = User.query.filter_by(id=args['user']).first()
            if not user:
                return {"data": "", "message": "用户不存在", "resCode": 1}
            followed_ids = [item.followed_id for item in
                            user.followed.all()]
            followed_ids.append(args['user'])
            authors = User.query.filter(
                not_(User.id.in_(followed_ids))).order_by(
                User.timestamp.desc()).paginate(
                args["page"], per_page=args["pre_page"], error_out=False
            )
        else:
            authors = User.query.filter().order_by(
                User.timestamp.desc()).paginate(
                args["page"], per_page=args["pre_page"], error_out=False
            )
        data = [marshal(item, UserListSerializer) for item in authors.items]
        page_info = {"pages": authors.pages, "total": authors.total}

        return {"data": data, "pageInfo": page_info, "message": "",
                "resCode": 0}


class Register(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("email", type=str, required=True, default="",
                                 trim=True, help="邮箱")
        self.parser.add_argument("username", type=str, required=True,
                                 default="", trim=True, help="用户名")
        self.parser.add_argument("password", type=str, required=True,
                                 default="", trim=True, help="密码")
        self.parser.add_argument("code", type=str, required=True,
                                 default="", trim=True, help="验证码")
        self.parser.add_argument("module", type=str, required=True,
                                 default="", trim=True, help="模块值",
                                 choices=["login", "register", "forget",
                                          "other"])

    def post(self):
        args = self.parser.parse_args()

        # 先查询是否存在
        user = User.query.filter(
            or_(User.email == args["email"],
                User.username == args["username"])).first()
        if user:
            return {"data": "", "message": "用户已注册", "resCode": 1}
        # 判断验证码
        code = get_redis_cahe(args["module"] + args["email"])
        if args["code"].upper() != code:
            return {"data": "", "message": "验证码错误", "resCode": 1}

        user = User(email=args["email"], username=args["username"],
                    password=args["password"])
        db.session.add(user)
        db.session.commit()

        return {"data": "", "message": "注册成功", "resCode": 0}


class SecurityCode(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("email", type=str, required=True, default="",
                                 trim=True, help="邮箱")
        self.parser.add_argument("module", type=str, required=True,
                                 default="", trim=True, help="模块值",
                                 choices=["login", "register", "forget",
                                          "other"])

    def get(self):
        args = self.parser.parse_args()

        # 生成验证码
        code = generate_code()
        # 发送邮箱
        send_mail(args["email"], '验证账号', code=code,
                  user=args["email"])

        # 验证码写入redis
        redis_params = {
            "key": args["module"] + args["email"],
            "value": code
        }
        _ = set_redis_cache(**redis_params)
        return {"data": "", "message": "邮箱验证", "resCode": 0}


class Login(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("email", type=str, required=True, default="",
                                 trim=True, help="邮箱")
        self.parser.add_argument("password", type=str, required=True,
                                 default="", trim=True, help="密码")
        # self.parser.add_argument("code", type=str, required=True,
        #                          default="", trim=True, help="密码")
        # self.parser.add_argument("module", type=str, required=True,
        #                          default="", trim=True, help="模块值",
        #                          choices=["login", "register", "forget",
        #                                   "other"])

    def post(self):
        args = self.parser.parse_args()

        # 先查询是否存在
        user = User.query.filter_by(email=args["email"]).first()
        # 验证用户是否存在
        if not user:
            return {"data": "", "message": "用户不存在", "resCode": 1}

        # 判断验证码
        # code = get_redis_cahe(args["module"] + args["email"])
        # if args["code"].upper() != code:
        #     return {"data": "", "message": "验证码错误", "resCode": 1}

        # 验证密码
        if not user.verify_password(args["password"]):
            return {"data": "", "message": "密码错误", "resCode": 1}

        # 获取token
        token = user.generate_token()
        data = {
            "token": token,
            "role": user.role.name,
            "username": user.username,
            "uid": user.id
        }
        return {"data": data, "message": "", "resCode": 0}


class UserFollow(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("user", type=int, required=True, help="用户Id")
        self.parser.add_argument("author", type=int, required=True,
                                 help="关注/取消关注作者Id")
        self.parser.add_argument("type", type=int, required=True,
                                 choices=[0, 1, 2],
                                 help="0:取消关注,1:关注,2:查看用户关注作者")

    def get(self):
        args = self.parser.parse_args()
        # 判断用户是否进行自我关注操作
        if args["user"] == args["author"]:
            return {"data": "", "message": "自我操作无效", "resCode": 1}
        # 判断用户是否存在
        user = User.query.filter_by(id=args["user"]).first()
        if not user:
            return {"data": "", "message": "无效用户", "resCode": 1}
        # 判断作者是否存在
        author = User.query.filter_by(id=args["author"]).first()
        if not author:
            return {"data": "", "message": "无效作者", "resCode": 1}

        # 判断取消关注
        if args["type"] == 0:
            # 判断用户是否关注过作者
            if user.is_following(author):
                user.unfollow(author)
                result = {"data": "取消关注", "message": "", "resCode": 0}
            else:
                result = {"data": "", "message": "你没有关注此作者", "resCode": 1}
        # 判断取消关注
        elif args["type"] == 1:
            if user.is_following(author):
                result = {"data": "", "message": "你已关注此作者", "resCode": 1}
            else:
                user.follow(author)
                result = {"data": "关注成功", "message": "", "resCode": 0}
        # 判断查看是否关注
        else:
            result = {"data": user.is_following(author), "message": "",
                      "resCode": 0}
        return result
