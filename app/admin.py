# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-4-17 下午3:19
from flask_admin.contrib.sqla import ModelView
from app.exts import db
from app.models import Role,User


def adminView(admin):
    admin.add_view(ModelView(Role, db.session, "权限"))
    admin.add_view(ModelView(User, db.session, "用户",endpoint="users"))
