# -*- coding: utf-8 -*-
# @Author: dmq
# @Time: 20-3-2 上午9:15
from flask_restful import Resource, reqparse, marshal
from app.models import User
from app import db
from app.email import send_mail
from app.utlis.tools import generate_code, set_redis_cache, get_redis_cache
from sqlalchemy import or_, not_
from app.user.serializers import UserListSerializer
from app.utlis.tools import build_es_query_params
from sqlalchemy import and_,desc,asc


class UserNewList(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("page", type=int, default=1, help="页数")
        self.parser.add_argument("per_page", type=int, default=10, help="每页数量")
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
                args["page"], per_page=args["per_page"], error_out=False
            )
        else:
            authors = User.query.filter().order_by(
                User.timestamp.desc()).paginate(
                args["page"], per_page=args["per_page"], error_out=False
            )
        data = [marshal(item, UserListSerializer) for item in authors.items]
        page_info = {"pages": authors.pages, "total": authors.total,
                     "page": authors.page, "per_page": authors.per_page,
                     "has_next": authors.has_next,
                     "has_prev": authors.has_prev}

        return {"data": data, "pageInfo": page_info, "message": "",
                "resCode": 0}


class Register(Resource):
    """用户注册"""
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
        code = get_redis_cache(args["module"] + args["email"])
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
    """用户登录"""
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("email", type=str, required=True, default="",
                                 trim=True, help="邮箱")
        self.parser.add_argument("password", type=str, required=True,
                                 default="", trim=True, help="密码")
    def post(self):
        args = self.parser.parse_args()

        # 先查询是否存在
        user = User.query.filter_by(email=args["email"]).first()
        # 验证用户是否存在
        if not user:
            return {"data": "", "message": "用户不存在", "resCode": 1}

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
    """关注 取消关注 判断用户是否关注"""
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
        if (args["user"] == args["author"]) and (args["type"] != 2):
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


class UserIndex(Resource):
    """用户信息"""
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("username", type=str, default="",
                                 trim=True, help="用户名")
        self.parser.add_argument("about_me", type=str, default="",
                                 trim=True, help="简介")
        self.parser.add_argument("topic", type=str, default="",
                                 trim=True, help="主题")
    def get(self, id):
        """获取用户信息"""
        user = User.query.filter_by(id=id).first()
        if not user:
            return {"data": "", "message": "用户不存在", "resCode": 1}
        data = {
            "name": user.username,
            "followed": user.followed.count(),
            "fans": user.followers.count(),
            "articles": user.article.count(),
            "about_me": user.about_me if user.about_me else '',
            "id": user.id,
            "topic": user.topic.split(",")
        }

        return {"data": data, "message": "", "resCode": 0}

    def put(self, id):
        """修改用户信息"""
        args = self.parser.parse_args()
        user = User.query.filter_by(id=id).first()
        user.username = args["username"]
        user.about_me = args["about_me"]
        user.topic = args["topic"]
        try:
            db.session.add(user)
            db.session.commit()
            result = {"data": "更新成功", "message": "", "resCode": 0}
        except Exception as ex:
            result = {"data": "", "message": "更新失败", "resCode": 0}
        return result


class UserIndexFollow(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("page", type=int, default=1, help="页数")
        self.parser.add_argument("per_page", type=int, default=10, help="每页数量")
        self.parser.add_argument("user", type=str, help="用户Id")
        self.parser.add_argument("type", type=str, required=True,
                                 default="fans", choices=["followed", "fans"],
                                 help="类型,followed:关注，fans:粉丝")

    def get(self, id):
        args = self.parser.parse_args()
        author = User.query.filter_by(id=id).first()
        if not author:
            return {"data": "", "message": "作者不存在", "resCode": 1}
        # 获取作者关注的人
        f_data = author.followed if args["type"] == "followed" \
            else author.followers
        f_data = f_data.paginate(
            args["page"], per_page=args["per_page"], error_out=False)
        data = []

        # 判断获取关注列表还是粉丝列表

        for item in f_data.items:
            f = item.followed if args["type"] == "followed" else item.follower
            tmp = {
                "id": f.id,
                "name": f.username,
                "followed": f.followed.count(),
                "fans": f.followers.count(),
                "articles": f.article.count(),
                "is_followed": True,
                "about_me":f.about_me
            }
            data.append(tmp)

        # 判断用户是否存在，用户不存在即匿名用户
        if args["user"]:
            user = User.query.filter_by(id=args["user"]).first()
            # 若用户和作者不想相等，则需要一个个去判断作者关注的人是否被用户关注
            if args["user"] != id:
                for i in data:
                    i["is_followed"] = user.is_following_by_id(i["id"])
        else:
            # 匿名用户所有为未关注
            for i in data:
                i["is_followed"] = False

        return {"data": data, "total": f_data.total, "message": "",
                "resCode": 0}


class UserHotList(Resource):
    """
    通过user获得topic,再将topic在es中进行聚合author
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
            "size": args["per_page"],
            "agg": True
        }

        # 构建es匹配语句
        search = build_es_query_params(**es_query_params)
        # 查询es
        resp = search.execute()
        # 获取匹配的文章ids
        author_ids = []
        data = []
        # 获取匹配的文章ids
        for i in resp.aggregations.author.buckets:
            author_ids.append(i["key"])
            data.append({
                "id": int(i["key"]),
                "count": i["doc_count"]
            })
        # 获取作者信息
        authors = User.query.filter(User.id.in_(author_ids)).all()
        author_dict = {i.id: i.username for i in list(authors)}
        # 加入作者姓名
        for i in data:
            i["name"] = author_dict.get(i["id"], "")

        return {"data": data, "message": "", "resCode": 0}


class UserSearchList(Resource):
    """用户搜索"""
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("page", type=int, default=1, help="页数")
        self.parser.add_argument("per_page", type=int, default=10, help="每页数量")
        self.parser.add_argument("user", type=str, help="用户Id")
        self.parser.add_argument("keywords", type=str, help="关键词,以逗号隔开")
        self.parser.add_argument("order", type=str, default="timestamp",
                                 trim=True, help="排序字段")
        self.parser.add_argument("sort", type=str, default="desc",
                                 choices=["desc", "asc"],
                                 trim=True, help="排序方式")

    def get(self):
        args = self.parser.parse_args()
        # 组装查询参数
        params = and_()
        if args["keywords"]:
            params = and_(params,
                          User.username.like("%" + args["keywords"] + "%"))
        sort = desc(args["order"]) if args["sort"] == "desc" else asc(
            args["order"])
        authors = User.query.filter(params).order_by(sort).paginate(
            args["page"], per_page=args["per_page"], error_out=False
        )
        if not authors.total:
            return {"data": [], "message": "", "resCode": 0}
        # 获取作者关注的人
        data = []
        for item in authors.items:
            tmp = {
                "id": item.id,
                "name": item.username,
                "about_me": item.about_me,
                "followed": item.followed.count(),
                "fans": item.followers.count(),
                "articles": item.article.count(),
                "is_followed": True
            }
            data.append(tmp)

        # 判断用户是否存在，用户不存在即匿名用户
        if args["user"]:
            user = User.query.filter_by(id=args["user"]).first()
            # 若用户和作者不想相等，则需要一个个去判断作者关注的人是否被用户关注
            if args["user"] != id:
                for i in data:
                    i["is_followed"] = user.is_following_by_id(i["id"])
        else:
            # 匿名用户所有为未关注
            for i in data:
                i["is_followed"] = False

        return {"data": data, "total": authors.total, "message": "",
                "resCode": 0}


class PwdUpdate(Resource):
    """密码修改"""

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("email", type=str, required=True, default="",
                                 trim=True, help="邮箱")
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
        user = User.query.filter(User.email == args["email"]).first()
        if not user:
            return {"data": "", "message": "用户不存在", "resCode": 1}
        # 判断验证码
        code = get_redis_cache(args["module"] + args["email"])
        if args["code"].upper() != code:
            return {"data": "", "message": "验证码错误", "resCode": 1}
        user.password = args["password"]
        db.session.add(user)
        db.session.commit()

        return {"data": "", "message": "修改成功", "resCode": 0}