# coding: utf-8
import threading
import time, os, sched
from flask import Flask
from flask.ext import restful
from flask.ext.pymongo import PyMongo
from flask import make_response
from bson.json_util import dumps
from pymongo import MongoClient
import feedparser
from time import mktime, strftime
from pyquery import PyQuery as pq
from datetime import datetime

MONGO_URL = os.environ.get('MONGO_URL')
if not MONGO_URL:
    MONGO_URL = "mongodb://localhost:27017/rss";

app = Flask(__name__)

app.config['MONGO_URI'] = MONGO_URL
mongo = PyMongo(app)

def output_json(obj, code, headers=None):
    resp = make_response(dumps(obj), code)
    resp.headers.extend(headers or {})
    return resp

DEFAULT_REPRESENTATIONS = {'application/json': output_json}
api = restful.Api(app)
api.representations = DEFAULT_REPRESENTATIONS


urls = ['http://rss.dailyfx.com.hk/cmarkets_chg_sc.xml',
        'http://rss.dailyfx.com.hk/commentary_morning_chg_sc.xml']

client = MongoClient(MONGO_URL)

def readRss(urls):
    posts = client.rss.readings
    print("refresh the news rss==")
    for url in urls:
        items = feedparser.parse(url)
        for entry in items.entries:
            if (posts.find_one({"link":entry.link})):
                continue

            str_pubDate = strftime("%Y-%m-%d %H:%M:%S",entry.date_parsed)
            d = pq(url=entry.link)
            content = d(".content").html()

            post={"title":entry.title, "link":entry.link,
                  "published":str_pubDate,
                  "date": datetime.fromtimestamp(mktime(entry.published_parsed)),
                  "summary":entry.summary,
                  'content':content}
            post_id = posts.insert(post)
            print post_id
    posts.create_index([("date", -1)])
    posts.create_index([("link", 1)])

def refreshRss():
    readRss(urls)
    print(time.ctime())
    threading.Timer(60*5, refreshRss).start()

refreshRss();

import flask_rest_service.resources
