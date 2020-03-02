# -*- coding: utf-8 -*-
# author: boe

from concurrent.futures.thread import ThreadPoolExecutor

from flask_redis import FlaskRedis
from mongoengine import connect
from pymongo import ReadPreference

from .init import config_module


# create mongodb client
if not config_module.DEBUG:
    uri = "mongodb://{user}:{password}@{hosts}/{db}?replicaSet={reps}"
else:
    if config_module.MONGODB["user"] and config_module.MONGODB["password"]:
        uri = "mongodb://{user}:{password}@{hosts}/{db}"
    else:
        uri = "mongodb://{host}:{port}/{db}"

mgo_client = connect(host=uri.format(**config_module.MONGODB),
                     read_preference=ReadPreference.PRIMARY_PREFERRED)

db = mgo_client.get_database(config_module.MONGODB["db"])

# create redis client
redis_client = FlaskRedis()

# create thread pool
pools = ThreadPoolExecutor(10)

# init audit rules
rules = list(db.tax_rules.find().sort("order"))
