# -*- coding: utf-8 -*-
# author: dmq

from concurrent.futures.thread import ThreadPoolExecutor

from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from elasticsearch import Elasticsearch
from config import config_module

# 数据库
db = SQLAlchemy()

# 邮箱
mail = Mail()

# create redis client
redis_client = FlaskRedis()

# create thread pool
pools = ThreadPoolExecutor(10)

es_client = Elasticsearch(hosts=config_module.ES_SETTING["hosts"], **{"timeout": 1000})