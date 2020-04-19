# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-4-17 下午3:19
from flask_admin.contrib.sqla import ModelView
from app.exts import db
from app.models import Role,User,Comment,Article,Follow


def adminView(admin):
    admin.add_view(ModelView(User, db.session, "用户",endpoint="users"))
    admin.add_view(ModelView(Article, db.session, "文章",endpoint="articles"))
    admin.add_view(ModelView(Comment, db.session, "评论",endpoint="comments"))
    admin.add_view(ModelView(Follow, db.session, "粉丝",endpoint="follows"))
    admin.add_view(ModelView(Role, db.session, "权限"))




