# coding: utf-8

from flask import Flask
from flask.ext import restful
from flask.ext.pymongo import PyMongo
from flask import make_response
from bson.json_util import dumps
import time, os

MONGO_URL = os.environ.get('MONGO_URL')
if not MONGO_URL:
    MONGO_URL = "mongodb://localhost:27017/rss"
    #MONGO_URL = "mongodb://rssuser:pwd123@mongo-atreeyang.myalauda.cn:10070/rss"

app = Flask(__name__)
print(MONGO_URL)
app.config['MONGO_URI'] = MONGO_URL
app.config['inited'] = 0
mongo = PyMongo(app)


def output_json(obj, code, headers=None):
    resp = make_response(dumps(obj), code)
    resp.headers.extend(headers or {})
    return resp

DEFAULT_REPRESENTATIONS = {'application/json': output_json}
api = restful.Api(app)
api.representations = DEFAULT_REPRESENTATIONS

import flask_rest_service.resources
