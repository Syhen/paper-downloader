# -*- coding: utf-8 -*-
"""
create on 2020-12-29 17:18
author @66492
"""
import json
import requests
from urllib import parse as urlparse

from lxml import etree

import os

import math

from paper_downloader import exceptions
from paper_downloader.agent.webvpn import WebVPNAgent
from paper_downloader.downloader.base import BaseDownloader
from paper_downloader.utils.encryto.aes import WebVPNEncoder
from paper_downloader.utils.encryto.md5 import md5


class DSSDownloader(BaseDownloader):
    domain = "https://www.sciencedirect.com/"

    def __init__(self, agent_cls=WebVPNAgent, encoder_cls=WebVPNEncoder, dir="C:/Users/66492/Desktop"):
        super(DSSDownloader, self).__init__(agent_cls=agent_cls, encoder_cls=encoder_cls, dir=dir)
        if self.domain is None:
            raise ValueError("please set `domain` when creating Downloader class.")

    def _extract_redirect_url(self, text):
        sel = etree.HTML(text=text)
        redirect_url = sel.xpath('//input[@name="redirectURL"]/@value')[0]
        return self.encoder.encode(urlparse.unquote(redirect_url))

    def _extract_pdf_url(self, redirect_url):
        text = self.agent.get(redirect_url).text
        data = json.loads(etree.HTML(text=text).xpath('//script[contains(.,"abstracts")]/text()')[0])
        article_data = data["article"]
        if "pdfDownload" not in article_data:
            raise exceptions.AccessDeny("your vpn were logged out, please log in and try again.")
        pdf_link = urlparse.urljoin(self.domain, article_data["pdfDownload"]["linkToPdf"])
        filename = data["article"]["titleString"]
        response = self.agent.get(self.encoder.encode(pdf_link))
        pdf_url = etree.HTML(response.text).xpath('//a/@href')[0]
        return pdf_url, filename

    def download(self, url: str, filename=None):
        """Download pdf file with given url

        :param url: str. dss pdf url, s.t. https://doi.org/10.1016/j.dss.2018.05.006
        :param filename: str or None. default None. If None, paper title will be used.
        :return: str. if succeed, return url of pdf file. else, raise exceptions.
        """
        self.agent.load_cookies()
        url = self.encoder.encode(url)
        redirect_url = self._extract_redirect_url(self.agent.get(url).text)
        pdf_url, pdf_name = self._extract_pdf_url(redirect_url)
        filename = filename if filename else pdf_name
        pdf_url = self.encoder.encode(pdf_url)
        self._download_pdf(pdf_url, filename)
        return pdf_url


class PaperListDownloader(object):
    def __init__(self, query, start_year=1991, end_year=2020, article_type="FLA%2CABS"):
        self.query_ = urlparse.quote(query)
        self.start_year_ = start_year
        self.end_year_ = end_year
        self.article_type_ = article_type
        self.agent = WebVPNAgent()

    def _download_single_list(self, url, years, offset, show=100):
        response = self.agent.get(url)
        data = response.json()["searchResults"]
        data_columns = ["doi", "openAccess", "title", "publicationDate", "pii"]

        def make_dict(i, data_columns):
            d = {"years": years, "offset": offset, "show": show}
            for k in data_columns:
                if k == "title":
                    sel = etree.HTML(text=i[k])
                    d[k] = sel.xpath("string(.)")
                else:
                    d[k] = i[k]
            return d

        return [make_dict(i, data_columns) for i in data]

    def _get_total_amount(self, url):
        filename = ".%s.tmp" % md5(url, size=16)
        if os.path.exists(filename):
            with open(filename, "r") as f:
                total_count, years, article_types, publication_titles = json.load(f)
            return total_count, years, article_types, publication_titles
        response = self.agent.get(url)
        data = response.json()
        total_count = data["resultsFound"]
        facets = data["facets"]
        years = facets["years"]
        article_types = facets["articleTypes"]
        publication_titles = facets["publicationTitles"]
        with open(filename, "w") as f:
            json.dump((total_count, years, article_types, publication_titles), f)
        return total_count, years, article_types, publication_titles

    def _condition_planning(self, total_count, years, article_types=None, publication_titles=None):
        tmp_count = 0
        idx = 0
        conditions = []
        tmp_years = []
        while 1:
            if idx == len(years):
                break
            data = years[idx]
            key = data["key"]
            count = data["value"]
            if tmp_count + count > 1000:
                conditions.append((",".join(sorted(tmp_years)), tmp_count))
                tmp_years = []
                tmp_count = 0
                continue
            tmp_count += count
            tmp_years.append(str(key))
            idx += 1
        if tmp_years:
            conditions.append((",".join(sorted(tmp_years)), tmp_count))
        if int(key) != self.start_year_:
            remain_count = total_count - sum(i["value"] for i in years)
            conditions.append((",".join(str(i) for i in range(self.start_year_, int(key))), remain_count))
        return conditions

    def _download_by_years(self, years, paper_count):
        show = 100
        # url_format = "https://www.sciencedirect.com/search/api?qs={query}&date={start}-{end}&years={years}&offset={offset}&show=100&articleTypes=FLA%2CABS&publicationTitles=271649%2C271700%2C271506%2C271680%2C271802%2C271692%2C271714&s"
        url_format = "https://www.sciencedirect.com/search/api?qs={query}&cid=272548&date={start}-{end}&years={years}&articleTypes=FLA&show=100&offset={offset}"
        datas = []
        for i in range(int(math.ceil(paper_count * 1. / 100))):
            offset = i * show
            url = url_format.format(query=self.query_, start=self.start_year_, end=self.end_year_,
                                    years=years, offset=offset)
            data = self._download_single_list(url, years, offset, show)
            datas.extend(data)
        return datas

    def download(self, url):
        # TODO: extract `url queries` from url & and to url_format
        # url = "https://www.sciencedirect.com/search/api?qs={query}&date={start}-{end}&offset=0&show=100"
        # url = url.format(query=self.query_, start=self.start_year_, end=self.end_year_)
        total_count, years, article_types, publication_titles = self._get_total_amount(url)
        print("total count:", total_count)
        conditions = self._condition_planning(total_count, years, article_types, publication_titles)
        datas = []
        for years, year_count in conditions:
            print(years, year_count)
            data = self._download_by_years(years, year_count)
            datas.extend(data)
        return datas

    def download_abstract(self, pii, timeout=None):
        url = "https://www.sciencedirect.com/science/article/abs/pii/{pii}?via=ihub".format(pii=pii)
        try:
            response = self.agent.get(url, timeout=timeout)
        except requests.exceptions.RequestException:
            return self.download_abstract(pii, timeout)
        # sel = etree.HTML(text=response.text)
        # redirect_url = urlparse.unquote(sel.xpath('//input[@name="redirectURL"]/@value')[0])
        # response = self.agent.get(redirect_url)
        sel = etree.HTML(text=response.text)
        journal = sel.xpath('//a[@class="publication-title-link"]/text()')[0]
        abstract = sel.xpath('//h2[contains(., "Abstract")]/following-sibling::div/p/text()')[0]
        keywords = sel.xpath('//div[@class="keyword"]/span/text()')
        data = {"journal": journal, "abstract": abstract, "keywords": keywords}
        return data


if __name__ == '__main__':
    import pandas as pd
    from tqdm import tqdm
    # https://doi.org/10.1016/j.acap.2020.08.013
    # dss_downloader = DSSDownloader()
    # print(dss_downloader.download("https://doi.org/10.1016/j.dss.2009.05.016", filename=None))
    # query = '("trader" OR "avatar") AND ("algorithm") AND ("competition")'

    # # query = '("trader" OR "human" OR "player" OR "avatar") AND ("algorithm" OR "machine" OR "agent" OR "computer") AND ("competition")'
    query = '("trader" OR "human" OR "player" OR "avatar") AND ("algorithm" OR "machine" OR "agent" OR "computer") AND ("competition")'
    paper_list_downloader = PaperListDownloader(query)
    # # url = "https://www.sciencedirect.com/search/api?qs={query}&date=1991-2020&articleTypes=FLA%2CABS&publicationTitles=271649%2C271700%2C271506%2C271680%2C271802%2C271692%2C271714&show=100&offset=800"
    # url = "https://www.sciencedirect.com/search/api?qs={query}&cid=272548&date=1991-2020&articleTypes=FLA&show=100"
    # url = url.format(query=query)
    # print(url)
    # data = paper_list_downloader.download(url)
    # pd.DataFrame(data).to_excel("jiewa_pii_2.xlsx", index=False)

    records = pd.read_excel("jiewa_pii_2.xlsx").to_dict("records")
    datas = []
    for record in tqdm(records):
        try:
            data = paper_list_downloader.download_abstract(record["pii"], timeout=10)
        except Exception:
            print(record)
            continue
        record.update(data)
        record["keywords"] = ",".join(record["keywords"])
        datas.append(record)
    pd.DataFrame(datas).to_excel("jiewa_abstract_2.xlsx", index=False)
