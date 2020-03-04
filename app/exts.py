# -*- coding: utf-8 -*-
# author: boe

from concurrent.futures.thread import ThreadPoolExecutor

from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from redis import Redis
from config import config_module

# 数据库
db = SQLAlchemy()

# 邮箱
mail = Mail()

# create redis client
redis_client = FlaskRedis()

redis_db = Redis(host='redis',port=6379)

# create thread pool
pools = ThreadPoolExecutor(10)
