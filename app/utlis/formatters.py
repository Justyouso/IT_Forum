# -*- coding: utf-8 -*-
# @Author: dmq
# @Time: 20-3-9 下午10:07

from bs4 import BeautifulSoup
from flask_restful import fields


class AuthorFormatter(fields.Raw):
    def format(self, value):
        return value.username


class CountFormatter(fields.Raw):
    def format(self, value):
        return value.count()


class BodyNumFormatter(fields.Raw):
    def format(self, value):
        return len(value)
