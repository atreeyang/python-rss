import urllib
import feedparser
import pymongo
from pymongo import MongoClient
import datetime
from pyquery import PyQuery as pq
from time import mktime, strftime
from datetime import datetime

client = MongoClient('localhost', 27017)
db = client.rss
posts = db.readings
#posts.drop()

#===========================================
urls = ['http://rss.dailyfx.com.hk/cmarkets_chg_sc.xml',
        'http://rss.dailyfx.com.hk/commentary_morning_chg_sc.xml']

def readRss(urls):
    print("refresh the news rss==")
    posts = mongo.db.readings
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
    posts.create_index([("date", -1)])
    posts.create_index([("link", 1)])

schedule = sched.scheduler(time.time, time.sleep)

def perform_command(cmd, inc):
    schedule.enter(inc, 0, perform_command, (cmd, inc))
    os.system(cmd)
    readRss(urls)

def timming_exe(cmd, inc = 60*10):
    schedule.enter(inc, 0, perform_command, (cmd, inc))
    schedule.run()

timming_exe("echo %time%")
#=====================================


readRss(urls)



#print getHtml("http://www.dailyfx.com.hk/commentary/morning-20150731-2779.html")
