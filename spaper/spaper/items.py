# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScienceDirectList(scrapy.Item):
    title = scrapy.Field()
    doi = scrapy.Field()
    years = scrapy.Field()
    offset = scrapy.Field()
    show = scrapy.Field()
    openAccess = scrapy.Field()
    publicationDate = scrapy.Field()
    pii = scrapy.Field()
    created_at = scrapy.Field()


class ScienceDirectDetail(ScienceDirectList):
    journal = scrapy.Field()
    abstract = scrapy.Field()
    keywords = scrapy.Field()


class AAAIDetail(scrapy.Item):
    title = scrapy.Field()
    abstract = scrapy.Field()
    category = scrapy.Field()
    unique_id = scrapy.Field()
    url = scrapy.Field()
    doi = scrapy.Field()
    year = scrapy.Field()
    pdf_url = scrapy.Field()
    journal = scrapy.Field()
    keywords = scrapy.Field()
    created_at = scrapy.Field()
