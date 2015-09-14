import os
from flask import Flask
from flask.ext import restful
from flask.ext.pymongo import PyMongo
from flask import make_response
from bson.json_util import dumps

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

tasks = [
    {
        'id': 1,
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol',
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial on the web',
        'done': False
    }
]

@app.route('/todo/api/v1.0/tasks', methods=['GET'])
def get_tasks():
    return  tasks

@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = filter(lambda t: t['id'] == task_id, tasks)
    return toJson({'task': task[0]})


urls = ['http://rss.dailyfx.com.hk/cmarkets_chg_sc.xml',
        'http://rss.dailyfx.com.hk/commentary_morning_chg_sc.xml'];

def readRss(urls):
    for url in urls:
        items = feedparser.parse(url)
        for entry in items.entries:
            d = pq(url=entry.link)
            content = d(".content").text().encode("utf-8")
            post={"title":entry.title, "link":entry.link,
                  "published":entry.published, "summary":entry.summary,
                  'content':content}
            post_id = posts.insert_one(post).inserted_id

if __name__ == '__main__':
    app.run(debug=True)
