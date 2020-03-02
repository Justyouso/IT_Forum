# -*- coding: utf-8 -*-
# author: boe

from flask import Blueprint
from flask_restful import Api
from app.user.views import UserList


user = Blueprint("user", __name__)
_api = Api(user)

_api.add_resource(UserList, "/tax/records/import")

