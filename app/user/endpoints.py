# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-2 上午9:15

from flask import Blueprint
from flask_restful import Api
from app.user.views import UserNewList, Register, SecurityCode, Login, \
    UserFollow,UserIndex,UserIndexFollow

user = Blueprint("user", __name__)
_api = Api(user)

# 最新文章列表
_api.add_resource(UserNewList, "/new/list")
# 注册
_api.add_resource(Register, "/register")
# 获取验证码
_api.add_resource(SecurityCode, "/code")
# 登录
_api.add_resource(Login, "/login")
# 判断是否关注
_api.add_resource(UserFollow, "/follow")
# 用户主页
_api.add_resource(UserIndex, "/index/<string:id>")
# 用户关注列表
_api.add_resource(UserIndexFollow, "/index/follows/<string:id>")
