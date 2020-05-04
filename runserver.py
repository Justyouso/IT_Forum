# -*- coding: utf-8 -*-
# @Author: dmq
# @Time: 20-3-2 上午11:06

from app import create_app
from config import config_module

app = create_app(config_module)

if __name__ == '__main__':
    app.run("0.0.0.0", debug=config_module.DEBUG)
