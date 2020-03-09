# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-9 下午10:07


from flask_restful import fields


class AuthorFormatter(fields.Raw):
    def format(self, value):
        return value.username


class CommentsFormatter(fields.Raw):
    def format(self, value):
        return value.count()
