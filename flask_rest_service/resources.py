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
               'entries':[x for x in mongo.db.readings.find().sort('date',-1).skip(offset).limit(limit)]}
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


urls = ['http://rss.dailyfx.com.hk/cmarkets_chg_sc.xml',
        'http://rss.dailyfx.com.hk/commentary_morning_chg_sc.xml']


client = MongoClient(app.config['MONGO_URI'])

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
            print(post_id)
    posts.create_index([("date", -1)])
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
        refreshRss()
        app.config['inited'] = 1
    return "init...."


api.add_resource(ReadingList, '/readings/')
api.add_resource(Reading, '/readings/<ObjectId:reading_id>')
