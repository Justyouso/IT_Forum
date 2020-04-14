# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-2 下午8:47

import random

from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MatchPhrase, Q
from jieba import analyse

from app import redis_client
from app.exts import es_client
from config import config_module


def set_redis_cache(key, value, time=600):
    """
    
    :param key: 键
    :param value: 值
    :param time: 缓存时间
    :return: 
    """
    result = True
    try:
        redis_client.set(key, value, time)
    except Exception as ex:
        result = False
    return result


def get_redis_cache(key):
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


def generate_words(string_list):
    """词云列表"""
    return [{"name": x, "value": w} for x, w in
            analyse.textrank(','.join(string_list), topK=200, withWeight=True)]


def build_es_query_params(topic=None, keywords=None, size=0, skip=0, agg=False):
    """
    
    :param topic: 用户的主题
    :param keywords: 关键词,以逗号隔开
    :param size: 每页多少条
    :param skip: 跳过多少条
    :param agg: 是否聚合
    :return: es_dsl
    """
    # 创建Search对象
    search = Search(using=es_client,
                    index=config_module.ES_SETTING["index"],
                    doc_type=config_module.ES_SETTING["index"])
    kws_query_dict = {}
    if topic:
        topic_kws_dict = [MatchPhrase(body_html=kw) for kw in topic.split(",")]
        kws_query_dict["topic"] = Q("bool", should=topic_kws_dict)

    if keywords:
        kws_dict = [MatchPhrase(body_html=kw) for kw in keywords.split(",")]
        kws_query_dict["keywords"] = Q("bool", should=kws_dict)

    search = search.source(["aggregations"])


    # 查询条件组装完成
    if kws_query_dict:
        search = search.query("bool",
                              must=[v for k, v in kws_query_dict.items()])
    else:
        search = search.query({"match_all": {}})

    if agg:
        search.aggs.bucket("author", "terms", size=100, field="author_id")

    # 添加其他参数
    other_params_dict = {}

    # 翻页 & 每页数量
    if skip != 0:
        other_params_dict.update({"from": skip})
    if size != 0:
        other_params_dict.update({"size": size})

    # 如果有聚合字段,不必返回匹配实体
    if agg:
        other_params_dict["size"] = 0

    # 设置最小分数
    other_params_dict["track_scores"] = True
    other_params_dict["min_score"] = 0

    if other_params_dict:
        search = search.update_from_dict(other_params_dict)
    return search
