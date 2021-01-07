# -*- coding: utf-8 -*-
"""
create on 2021-01-06 14:47
author @66492
"""
import json
from scrapy.spiders import Spider

from spaper.items import ScienceDirectList, ScienceDirectDetail


class ScientDirectListSpider(Spider):
    name = "science_direct_list"

    def parse(self, response, **kwargs):
        data = json.loads(response.text)
        return
