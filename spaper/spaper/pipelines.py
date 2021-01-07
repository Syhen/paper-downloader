# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from urllib import parse as urlparse

import pymongo
from datetime import datetime
from scrapy.spiders import Spider

from itemadapter import ItemAdapter


class SpaperPipeline:
    def open_spider(self, spider):
        self.client_ = pymongo.MongoClient()
        self.db_ = self.client_["papers"]

    def close_spider(self, spider):
        self.client_.close()

    def process_item(self, item, spider: Spider):
        if spider.name == "science_direct_list":
            self.db_["science_direct_list"].update_one({"_id": item["doi"]}, {"$set": item}, upsert=True)
            return item
        if spider.name == "science_direct_detail":
            keywords = item.get("keywords", None)
            if keywords:
                item["keywords"] = ",".join(keywords)
            item["created_at"] = datetime.now()
            self.db_["science_direct_list"].update_one({"_id": item["doi"]}, {"$set": item}, upsert=True)
            return item
        if spider.name == "aaai_detail":
            keywords = item.get("keywords", None)
            if keywords:
                item["keywords"] = ",".join(keywords)
            item["created_at"] = datetime.now()
            item["doi"] = urlparse.urlsplit(item["doi"]).path[1:].strip()
            self.db_["aaai_list"].update_one({"_id": item["unique_id"]}, {"$set": item}, upsert=True)
            return item
        return item
