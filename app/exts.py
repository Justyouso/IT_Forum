# -*- coding: utf-8 -*-
# author: boe

from concurrent.futures.thread import ThreadPoolExecutor

from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

# 数据库
db = SQLAlchemy()

# 邮箱
mail = Mail()

# create redis client
redis_client = FlaskRedis()

# create thread pool
pools = ThreadPoolExecutor(10)
