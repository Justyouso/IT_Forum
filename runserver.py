# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-2 上午11:06

from app import create_app
from config import config_flag

app = create_app(config_flag)

if __name__ == '__main__':
    app.run("0.0.0.0", debug=True)