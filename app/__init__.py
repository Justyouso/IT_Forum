# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-2 上午9:12

from flask import Flask
from werkzeug.utils import import_string

from app.exts import db, redis_client,mail
from config import config


def register_extensions(app):
    redis_client.init_app(app)


def register_blueprints(app, blueprints: list):
    for bp in blueprints:
        module = import_string(bp)
        app.register_blueprint(module, url_prefix="/" + bp.split(":")[1])


def register_middleware(app, middlewares):
    # app.wsgi_app = middlewares(app.wsgi_app)
    pass


business_modules = [
    "app.user:user"
]


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    # db
    db.init_app(app)
    # mail
    mail.init_app(app)
    # redis
    redis_client.init_app(app)
    # register_middleware(app, AuthMiddleware)
    # register_extensions(app)
    register_blueprints(app, business_modules)
    return app
