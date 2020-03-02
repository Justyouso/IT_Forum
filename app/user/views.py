# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-2 上午9:15
from flask_restful import Resource, reqparse


class UserList(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("page", type=int, default=1, help="页数")
        self.parser.add_argument("offset", type=int, default=10, help="每页数量")
        self.parser.add_argument("name", type=str, default="", trim=True,
                                 help="方案名称")
        self.parser.add_argument("dept", type=str, default="", trim=True,
                                 help="所属部门ID")
        self.parser.add_argument("user", type=str, default="", trim=True,
                                 help="所属用户ID")
        self.parser.add_argument("sortby", type=str, default="order", trim=True,
                                 help="排序字段")
        self.parser.add_argument("order", type=str, default="asc", trim=True,
                                 choices=["asc", "desc"], help="升降序")
        self.parser.add_argument("sources", type=str, trim=True, default="",
                                 help="返回字段")

    def get(self):
        return {"data": ""}, 200
