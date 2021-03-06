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

class ReadingList(restful.Resource):
    def __init__(self, *args, **kwargs):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('reading', type=str)
        super(ReadingList, self).__init__()

    def get(self):
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 20))
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

@app.route('/init')
def init():
    inited = app.config['inited']
    if (inited == 0):
        threading.Timer(5, refreshRss).start()
        app.config['inited'] = 1
    else:
        threading.Timer(5, refreshRss).start()
        return "already inited"
    return "init...."

@app.route('/feedback/', methods=['POST'])
def feedback():
    client = MongoClient(app.config['MONGO_URI'])
    contact = request.args.get('contact', '')
    content = request.args.get('content', '')
    feedback = client.get_default_database().feedbacks
    feedback.insert({'contact':contact, 'content':content})
    return "success"

@app.route('/getFeedback/')
def getFeedback():
    res = {'status':0,
           'entries':[x for x in mongo.db.feedbacks.find()]}
    print(res)
    return  res


class MyFeedback(restful.Resource):
    def get(self):
        res = {'status':0,
               'entries':[x for x in mongo.db.feedbacks.find()]}
        return res


api.add_resource(MyFeedback, '/myfeedback/')
api.add_resource(ReadingList, '/readings/')
api.add_resource(Reading, '/readings/<ObjectId:reading_id>')


from urlparse import urljoin
from werkzeug.contrib.atom import AtomFeed


def make_external(url):
    return urljoin(request.url_root, url)


@app.route('/recent.atom')
def recent_feed():
    feed = AtomFeed('dailyfx summary',
                    feed_url=request.url, url=request.url_root)
    offset = 0
    limit = 200
    cat = 'DailyFx'
    articles = [ x for x in mongo.db.readings.find({'cat':cat},{'title':1,'content':1,'published':1,'subcat':1, 'date':1, 'published':1}).sort('date',-1).skip(offset).limit(limit)]

    for article in articles:
        if(article['title'] is None):
            continue;
        feed.add(article['title'], unicode(article['content']),
                 content_type='html',
                 author=article['subcat'],
                 url=make_external('http://atreeyang-rss2.daoapp.io/readings/' + str(article['_id'])),
                 updated=article['date'],
                 published=datetime.strptime(article['published'], "%Y-%m-%d %H:%M"))
    return feed.get_response()
