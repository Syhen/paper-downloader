# -*- coding: utf-8 -*-
"""
create on 2021-01-06 14:50
author @66492
"""
import pandas as pd
import scrapy
from scrapy.spiders import Spider

from spaper.items import ScienceDirectDetail


class ScientDirectDetailSpider(Spider):
    name = "science_direct_detail"

    def start_requests(self):
        # df = pd.read_excel(r"C:\Users\66492\Documents\paper-downloader\paper_downloader\downloader\jiewa_pii.xlsx")
        # records = df.to_dict("records")
        df = pd.read_excel(r"C:\Users\66492\Desktop\jiewa-science-direct.xlsx")
        records = df.to_dict("records")
        self.logger.debug("len of data: %s" % len(records))
        for record in records:
            if isinstance(record["abstract"], float):
                url = "https://www.sciencedirect.com/science/article/abs/pii/{pii}?via=ihub".format(pii=record["pii"])
                yield scrapy.Request(url, callback=self.parse, meta={"data": record})

    def parse(self, response, **kwargs):
        item = ScienceDirectDetail()
        item.update(response.meta["data"])
        journal = response.xpath('//a[@class="publication-title-link"]/text()').get()
        abstract = response.xpath('//h2[contains(., "Abstract")]/following-sibling::div/p/.').get()
        if not abstract:
            abstract = response.xpath('string(//div[@id="abstracts"]/div[2]//p/.)').get()
        keywords = response.xpath('//div[@class="keyword"]/span/text()').extract()
        item["journal"] = journal
        item["abstract"] = abstract
        item["keywords"] = keywords
        return item
