# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ArtstationComItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    model_url = scrapy.Field()
    model_id = scrapy.Field()
    url = scrapy.Field()
    hash_id = scrapy.Field()
    title = scrapy.Field()
