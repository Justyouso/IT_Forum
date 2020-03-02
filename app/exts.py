# -*- coding: utf-8 -*-
# author: boe

from concurrent.futures.thread import ThreadPoolExecutor

from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# create redis client
redis_client = FlaskRedis()

# create thread pool
pools = ThreadPoolExecutor(10)
