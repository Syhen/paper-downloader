# -*- coding: utf-8 -*-
"""
create on 2021-01-06 14:50
author @66492
"""
import pymongo
import pandas as pd
import scrapy
from scrapy.spiders import Spider

from spaper.items import AAAIDetail


class AAAIDetailSpider(Spider):
    name = "aaai_detail"

    def start_requests(self):
        df = pd.read_excel(r"C:\Users\66492\Documents\paper-downloader\paper_downloader\downloader\aaai-list.xlsx")
        records = df.to_dict("records")
        client = pymongo.MongoClient()
        db = client["papers"]
        data = db.aaai_list.find({})
        data = set([i["_id"] for i in data])
        skip_num = 0
        for record in records:
            url = record.pop("url_detail")
            if record["unique_id"] in data:
                skip_num += 1
                continue
            if not url or url.endswith(".pdf"):
                skip_num += 1
                continue
            record["url"] = url
            yield scrapy.Request(url, callback=self.parse, meta={"data": record})
        self.logger.debug(
            "total amount: %s, skip num: %s, download amount: %s" % (len(records), skip_num, len(records) - skip_num))
        # yield scrapy.Request(
        #     "http://www.aaai.org/ocs/index.php/DC/DC10/paper/view/1632",
        #     callback=self.parse,
        #     dont_filter=True,
        #     meta={"data": {"unique_id": "63e98d88fea98b82b8c73e8f75ec82b9"}}
        # )

    def parse(self, response: scrapy.http.Response, **kwargs):
        item = AAAIDetail()
        item.update(response.meta["data"])
        journal = "aaai"
        abstracts = [i.xpath("string(.//.)").get("").strip() for i in
                     response.xpath('//section[@class="item abstract"]/p')]
        doi = response.xpath('//section[@class="item doi"]/span/a/text()').get("").strip()
        pdf_url = ""
        if not abstracts:
            pdf_finder = response.xpath('//div[@id="abstract"]/h1/a/@href').extract()
            if pdf_finder:
                # https://aaai.org/Library/IAAI/2008/iaai08-005.php
                abstracts = response.xpath('//div[@id="abstract"]/p[not(@class or @id)]/text()').extract()
                pdf_url = response.urljoin(pdf_finder[0])
            else:
                # https://www.aaai.org/ocs/index.php/AAAI/AAAI10/paper/view/1875
                abstracts = response.xpath('string(//div[@id="abstract"]/div/.)').extract()
                pdf_finder = response.xpath('//div[@id="paper"]/a/@href').extract()
                if not pdf_finder and not response.url.endswith(".php"):
                    # not find, redirect to `viewPaper` page with `https` scheme.
                    self.logger.debug(b",".join(response.request.headers.keys()).decode())
                    self.logger.debug("referer from: " + response.request.headers.get("Referer", b"").decode())
                    return scrapy.Request(
                        response.url.replace("/view/", "/viewPaper/").replace("http:", "https:"),
                        # dont_filter=True,
                        callback=self.parse,
                        meta=response.meta
                    )
                if pdf_finder:
                    pdf_url = response.urljoin(pdf_finder[0])
        abstract = "\n".join(abstracts)
        keywords = []
        item["doi"] = doi
        item["journal"] = journal
        item["abstract"] = abstract
        item["keywords"] = keywords
        if pdf_url:
            item["pdf_url"] = pdf_url
        return item
