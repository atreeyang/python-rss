import urllib
import feedparser
import pymongo
from pymongo import MongoClient
import datetime
from pyquery import PyQuery as pq

urls = ['http://rss.dailyfx.com.hk/cmarkets_chg_sc.xml',
        'http://rss.dailyfx.com.hk/commentary_morning_chg_sc.xml'];

client = MongoClient('localhost', 27017)
db = client.rss
posts = db.readings
posts.drop()

def readRss(urls):
    i = 0
    for url in urls:
        items = feedparser.parse(url)
        for entry in items.entries:
            d = pq(url=entry.link)
            content = d(".content").html()
            post={"title":entry.title, "link":entry.link,
                  "published":entry.published, "summary":entry.summary,
                  'content':content}
            post_id = posts.insert_one(post).inserted_id


def getHtml(url):
    page = urllib.urlopen(url)
    html = page.read()
    return html

readRss(urls)
print posts.find_one()


#print getHtml("http://www.dailyfx.com.hk/commentary/morning-20150731-2779.html")
