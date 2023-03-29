# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
from settings import mongo_host,mongo_port, mongo_user, mongo_password, mongo_db, mongo_cli
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class ArtstationComPipeline:
    def __init__(self):
        self.mongo_cli = pymongo.MongoClient(host=mongo_host, port=mongo_port, username=mongo_user, password=mongo_password)

    def process_item(self, item, spider):
        db = self.mongo_cli[mongo_db]
        cli = db[mongo_cli]
        item = dict(item)
        item['is_play'] = 0
        cli.insert_one(dict(item))
        return item
