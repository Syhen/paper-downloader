# -*- coding: utf-8 -*-
"""
create on 2021-01-07 13:26
author @66492
"""
import requests
from urllib import parse as urlparse

from lxml import etree

from paper_downloader.agent.webvpn import WebVPNAgent
from paper_downloader.utils.encryto.md5 import md5


class AAAIPaperListDownloader(object):
    def __init__(self):
        self.agent = WebVPNAgent()

    def _download_single_list(self, url, meta_data=None):
        meta_data = meta_data or {}
        response = self.agent.get(url)
        if response.status_code == 404:
            return []
        sel = etree.HTML(text=response.text)
        content = sel.xpath('//div[@class="content"]')[0]
        papers = content.xpath("./*")
        category = None
        for paper in papers:
            if paper.tag != "p":
                category_filter = paper.xpath('./h4/text()') or paper.xpath('./text()') or paper.xpath('./a/text()')
                if category_filter:
                    category = category_filter[0]
                    continue
            if not category:
                continue
            pdf_url = paper.xpath('./a[contains(.,"PDF")]/@href')
            pdf_url = urlparse.urljoin(response.url, pdf_url[0]) if pdf_url else ""
            url_detail = paper.xpath('./a/@href')
            url_detail = urlparse.urljoin(response.url, url_detail[0]) if url_detail else ""
            if not url_detail:
                continue
            data = {
                "url_detail": url_detail,
                "title": paper.xpath('./a/text()')[0].strip(),
                "pdf_url": pdf_url,
                "category": category,
                "unique_id": md5(url_detail)
            }
            data.update(meta_data)
            yield data

    def download_list(self):
        for year in range(20):
            url = "https://aaai.org/Library/AAAI/aaai{year:0>2}contents.php".format(year=year)
            yield {"url": url, "year": year}
        for i in range(1, 11):
            url = "https://aaai.org/Library/AAAI/aaai20contents-issue{issue:0>2}.php".format(issue=i)
            yield {"url": url, "year": 20}
        for year in range(80, 100):
            url = "https://aaai.org/Library/AAAI/aaai{year:0>2}contents.php".format(year=year)
            yield {"url": url, "year": year}

    def download_abstract(self, url, timeout=None):
        pass


if __name__ == '__main__':
    import pandas as pd
    from tqdm import tqdm

    aaai_paper_list_downloader = AAAIPaperListDownloader()
    aaai_list = aaai_paper_list_downloader.download_list()
    datas = []
    for meta in tqdm(list(aaai_list)):
        datas.extend(list(aaai_paper_list_downloader._download_single_list(meta.pop("url"), meta)))
    pd.DataFrame(datas).to_excel("aaai-list.xlsx", index=False)
