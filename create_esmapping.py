# -*- coding: utf-8 -*-
# @Author: dmq
# @Time: 20-3-23 下午5:40
# coding=utf-8
from config import  config_module
from elasticsearch import Elasticsearch
ES_HOSTS = config_module.ES_SETTING["hosts"]
INDEX_NAME = config_module.ES_SETTING["index"]
DOC_TYPE = config_module.ES_SETTING["doc_type"]

es = Elasticsearch(hosts=ES_HOSTS)

res = es.indices.delete(index=INDEX_NAME)

request_body = {
    "mappings": {
        DOC_TYPE: {
            "properties": {
                "body_html": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_max_word"
                },
                "author": {
                    "type": "keyword"
                },
                "author_id": {
                    "type": "keyword"
                }
            }
        }
    }
}

res = es.indices.create(index=INDEX_NAME, ignore=400, body=request_body)
print(" response: {}".format(res))