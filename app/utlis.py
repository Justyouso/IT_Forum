# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-2 下午8:47

# from app import redis_client
from app.exts import redis_db as redis_client

import random


def set_redis_cache(key, value, time=600):
    """
    
    :param key: 键
    :param value: 值
    :param time: 缓存时间
    :return: 
    """
    import json
    result = True
    try:
        redis_client.set(key, value, time)
    except Exception as ex:
        result = False
    return result


def get_redis_cahe(key):
    return redis_client.get(key).decode()


def generate_code():
    """
    生成6位随机验证码
    :return: 
    """
    code = ''
    for i in range(6):
        current = random.randrange(0, 4)
        if current != i:  # !=  不等于 - 比较两个对象是否不相等
            temp = chr(random.randint(65, 90))
        else:
            temp = random.randint(0, 9)
        code += str(temp)
    return code
