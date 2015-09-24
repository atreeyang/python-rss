# coding: utf-8
import urllib2
import StringIO
import gzip
import json
from flask import request, abort
from flask.ext import restful
from flask.ext.restful import reqparse
from flask_rest_service import app, api, mongo
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

import logging

FILE = os.getcwd()
logging.basicConfig(filename=os.path.join(FILE,'flask_rest_service/static/log.log'),
                    level=logging.DEBUG,format='%(asctime)s:%(message)s',datefmt='%m/%d/%Y %I:%M:%S %p')


class ReadingList(restful.Resource):
    def __init__(self, *args, **kwargs):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('reading', type=str)
        super(ReadingList, self).__init__()

    def get(self):
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 20))
        print(offset)
        print(limit)
        cat = request.args.get('cat', 'dailyfx')
        res = {'status':0,
               'entries':[x for x in mongo.db.readings.find({'cat':cat},{'title':1,'published':1,'subcat':1})
                          .sort('date',-1).skip(offset).limit(limit)]}
        return  res


    def post(self):
        args = self.parser.parse_args()
        if not args['reading']:
            abort(400)

        jo = json.loads(args['reading'])
        reading_id =  mongo.db.readings.insert(jo)
        return mongo.db.readings.find_one({"_id": reading_id})

class Reading(restful.Resource):
    def get(self, reading_id):
        return mongo.db.readings.find_one_or_404({"_id": reading_id})

    def delete(self, reading_id):
        mongo.db.readings.find_one_or_404({"_id": reading_id})
        mongo.db.readings.remove({"_id": reading_id})
        return '', 204



@app.route('/entry/<ObjectId:id>')
def entry_detail(id):
    print(id)
    entry = mongo.db.readings.find_one({'_id': id})
    print(entry)
    return render_template('entry.html', entry=entry)


urls = [{'cat':'DailyFx', 'subcat':'市场回音', 'url':'http://rss.DailyFx.com.hk/cmarkets_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'纽约盘后', 'url':'http://rss.DailyFx.com.hk/commentary_morning_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'欧洲盘前', 'url':'http://rss.DailyFx.com.hk/commentary_afternoon_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'纽约盘前', 'url':'http://rss.DailyFx.com.hk/commentary_evening_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'美元指数', 'url':'http://rss.DailyFx.com.hk/us_dollar_index_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'美元指数技术分析', 'url':'http://rss.DailyFx.com.hk/us_dollar_index_techs_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'外汇名家', 'url':'http://rss.DailyFx.com.hk/analysts_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'技术分析', 'url':'http://rss.DailyFx.com.hk/techs_chg_sc.xml'},
        #{'cat':'DailyFx', 'subcat':'论交叉盘', 'url':'http://rss.DailyFx.com.hk/crosses_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'直盘分析', 'url':'http://rss.DailyFx.com.hk/charts_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'今日看盘', 'url':'http://rss.DailyFx.com.hk/intraday_techs_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'牛熊榜', 'url':'http://rss.DailyFx.com.hk/winners_and_losers_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'专题探讨', 'url':'http://rss.DailyFx.com.hk/feaarticle_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'期货变化', 'url':'http://rss.DailyFx.com.hk/cotreport_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'投机情绪指数', 'url':'http://rss.DailyFx.com.hk/fxcmssi_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'每周基本分析展望', 'url':'http://rss.DailyFx.com.hk/outlook_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'每周交易策略', 'url':'http://rss.DailyFx.com.hk/weekly_strategy_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'金属产品', 'url':'http://rss.DailyFx.com.hk/metal_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'股市原油', 'url':'http://rss.DailyFx.com.hk/stocks_oil_chg_sc.xml'},
        {'cat':'DailyFx', 'subcat':'机构报告', 'url':'http://rss.DailyFx.com.hk/institution_chg_sc.xml'}]

client = MongoClient(app.config['MONGO_URI'])
def log(msg):
    logging.warning(msg)

def readRss(urls):
    posts = client.get_default_database().readings
    for url in urls:
        items = feedparser.parse(url['url'])
        try:
            for entry in items.entries:
                if (posts.find_one({"link":entry.link})):
                    break
                str_pubDate = strftime("%Y-%m-%d %H:%M",entry.date_parsed)
                log(entry.link)
                d = pq(readHtml(entry.link))
                content = d(".content").html()
                post={"title":entry.title, "link":entry.link,
                      "published":str_pubDate,
                      "date": datetime.fromtimestamp(mktime(entry.published_parsed)),
                      #"summary":entry.summary,
                      'cat':url['cat'],
                      'subcat':url['subcat'],
                      'content':content}
                post_id = posts.insert(post)
                log(post_id)
        except Exception as e:
            log(e)

    posts.create_index([("date", -1)])
    posts.create_index([("cat", -1)])
    posts.create_index([("link", 1)])

def refreshRss():
    while True:
        log("begin refresh rss")
        rssZeroHedge()
        readRss(urls)
        log("finish refresh rss")
        time.sleep(1000 * 10)

t = threading.Thread(target=refreshRss)
t.start()

def readHtml(link):
    r = requests.get(link)
    r.encoding = "utf-8"
    return r.text

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
    html = readHtml("http://www.zerohedge.com")
    d = pq(html)
    content = d(".js-l1")

    for entry in content:
        div = pq(entry)
        dataUrl = div('a').attr('data-url')
        dataTitle = div('a').attr('data-text')
        if (posts.find_one({"link":dataUrl})):
            break;

        page = pq(readHtml(dataUrl))
        log(dataUrl)
        node = page("div.node")
        content = node("div.content").html()
        str_pubDate = strftime("%Y-%m-%d %H:%M",time.localtime())
        post={"title":dataTitle, "link":dataUrl,
                      "published":str_pubDate,
                      "date": datetime.fromtimestamp(time.time()),
                      'cat':'ZeroHedge',
                      'subcat':'',
                      'content':content}
        post_id = posts.insert(post)
        log(post_id)

@app.route('/init')
def init():
    inited = app.config['inited']
    log(inited)
    if (inited == 0):
        threading.Timer(5, refreshRss).start()
        app.config['inited'] = 1
    else:
        threading.Timer(5, refreshRss).start()
        return "already inited"
    return "init...."

@app.route('/clear')
def clear():
    client.get_default_database().readings.drop()
    return "clear...."


api.add_resource(ReadingList, '/readings/')
api.add_resource(Reading, '/readings/<ObjectId:reading_id>')
