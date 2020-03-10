# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-2 上午9:15

from flask import Blueprint
from flask_restful import Api
from app.user.views import UserNewList, Register, SecurityCode, Login

user = Blueprint("user", __name__)
_api = Api(user)

_api.add_resource(UserNewList, "/new/list")
_api.add_resource(Register, "/register")
_api.add_resource(SecurityCode, "/code")
_api.add_resource(Login, "/login")
