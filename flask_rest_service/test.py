import urllib2
import StringIO
import gzip
import StringIO
import gzip

import json
from flask import request, abort
from flask.ext import restful
from flask.ext.restful import reqparse
from bson.objectid import ObjectId
from flask import Flask, render_template
from pymongo import MongoClient
import feedparser
from time import mktime, strftime
from pyquery import PyQuery as pq
from datetime import datetime
import time, os, sched
import threading
import sys
import requests

reload(sys)
sys.setdefaultencoding('utf-8')
MONGO_URL = "mongodb://localhost:27017/rss"
client = MongoClient(MONGO_URL)

#link = "http://www.baidu.com"
def readZipUrl(link):
    req = urllib2.Request(link)
    opener = urllib2.build_opener()
    response = opener.open(req)
    data = response.read()
    data = StringIO.StringIO(data)
    gzipper = gzip.GzipFile(fileobj=data)
    html = gzipper.read()
    return html

def rssZeroHedge():
    posts = client.get_default_database().readings
    html = readZipUrl("http://www.zerohedge.com")
    d = pq(html)
    content = d(".js-l1")

    for entry in content:
        div = pq(entry)
        dataUrl = div('a').attr('data-url')
        dataTitle = div('a').attr('data-text')
        if (posts.find_one({"link":dataUrl})):
            break;
        page = pq(url=dataUrl)
        print dataUrl
        node = page("div.node")
        content = node("div.content").html().encode("utf-8")
        str_pubDate = strftime("%Y-%m-%d %H:%M",time.localtime())
        post={"title":dataTitle, "link":dataUrl,
                      "published":str_pubDate,
                      "date": datetime.fromtimestamp(time.time()),
                      #"summary":entry.summary,
                      'cat':'zeroHedge',
                      'subcat':'',
                      'content':content}
        post_id = posts.insert(post)
        print(post_id)

rssZeroHedge()
