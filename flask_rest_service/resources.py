# coding: utf-8

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
        res = {'status':0,
               'entries':[x for x in mongo.db.readings.find({},{'title':1,'published':1,'subcat':1})
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


urls = [{'cat':'dailfx', 'subcat':'市场回音', 'url':'http://rss.dailyfx.com.hk/cmarkets_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'纽约盘后', 'url':'http://rss.dailyfx.com.hk/commentary_morning_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'欧洲盘前', 'url':'http://rss.dailyfx.com.hk/commentary_afternoon_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'纽约盘前', 'url':'http://rss.dailyfx.com.hk/commentary_evening_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'美元指数', 'url':'http://rss.dailyfx.com.hk/us_dollar_index_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'美元指数技术分析', 'url':'http://rss.dailyfx.com.hk/us_dollar_index_techs_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'外汇名家', 'url':'http://rss.dailyfx.com.hk/analysts_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'技术分析', 'url':'http://rss.dailyfx.com.hk/techs_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'论交叉盘', 'url':'http://rss.dailyfx.com.hk/crosses_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'直盘分析', 'url':'http://rss.dailyfx.com.hk/charts_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'今日看盘', 'url':'http://rss.dailyfx.com.hk/intraday_techs_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'牛熊榜', 'url':'http://rss.dailyfx.com.hk/winners_and_losers_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'专题探讨', 'url':'http://rss.dailyfx.com.hk/feaarticle_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'期货变化', 'url':'http://rss.dailyfx.com.hk/cotreport_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'投机情绪指数', 'url':'http://rss.dailyfx.com.hk/fxcmssi_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'每周基本分析展望', 'url':'http://rss.dailyfx.com.hk/outlook_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'每周交易策略', 'url':'http://rss.dailyfx.com.hk/weekly_strategy_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'金属产品', 'url':'http://rss.dailyfx.com.hk/metal_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'股市原油', 'url':'http://rss.dailyfx.com.hk/stocks_oil_chg_sc.xml'},
        {'cat':'dailfx', 'subcat':'机构报告', 'url':'http://rss.dailyfx.com.hk/institution_chg_sc.xml'}]


client = MongoClient(app.config['MONGO_URI'])

def readRss(urls):
    posts = client.get_default_database().readings
    print("refresh the news rss==")
    for url in urls:
        items = feedparser.parse(url['url'])
        try:
            for entry in items.entries:
                if (posts.find_one({"link":entry.link})):
                    break

                str_pubDate = strftime("%Y-%m-%d %H:%M",entry.date_parsed)
                d = pq(url=entry.link)
                content = d(".content").html()

                post={"title":entry.title, "link":entry.link,
                      "published":str_pubDate,
                      "date": datetime.fromtimestamp(mktime(entry.published_parsed)),
                      #"summary":entry.summary,
                      'cat':url['cat'],
                      'subcat':url['subcat'],
                      'content':content}
                post_id = posts.insert(post)
                print(post_id)
        except e:
            print(e)

    posts.create_index([("date", -1)])
    posts.create_index([("cat", -1)])
    posts.create_index([("link", 1)])

def refreshRss():
    readRss(urls)
    print(time.ctime())
    threading.Timer(60*5, refreshRss).start()

@app.route('/init')
def init():
    inited = app.config['inited']
    print(inited)
    if (inited == 0):
        threading.Timer(5, refreshRss).start()
        app.config['inited'] = 1
    else:
        return "already inited"
    return "init...."

@app.route('/clear')
def clear():
    client.get_default_database().readings.drop()
    return "clear...."


api.add_resource(ReadingList, '/readings/')
api.add_resource(Reading, '/readings/<ObjectId:reading_id>')
