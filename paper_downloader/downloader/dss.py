# -*- coding: utf-8 -*-
"""
create on 2020-12-29 17:18
author @66492
"""
import json
import requests
import warnings
from urllib import parse as urlparse

from lxml import etree

import os

import math

from paper_downloader import exceptions
from paper_downloader.agent.webvpn import WebVPNAgent
from paper_downloader.downloader.base import BaseDownloader
from paper_downloader.utils.encryto.aes import WebVPNEncoder
from paper_downloader.utils.encryto.md5 import md5
from paper_downloader.utils.url_parse import query_decode


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


class DSSPaperListDownloader(object):
    """Downloader of search result from `https://www.sciencedirect.com/search`

    Review tools for get paper title and abstract of your condition.
    """
    def __init__(self, query, start_year=1991, end_year=2020, subject_areas=None, article_type=None,
                 publication_title=None):
        """Initial of downloader. **It is recommended to use `from_url` class method.**

        :param query: str. query string. query use in the `https://www.sciencedirect.com/search`.
        :param start_year: int. start year.
        :param end_year: int. end year.
        :param subject_areas: str. subject area filter of site. (Area)
        :param article_type: str. article type filter of site. (Review, Research and Others)
        :param publication_title: str. publication title of site. (Journal)

        Note that `subject_areas`, `article_type` and `publication title` is encoded by the site.
        Note: `publication title` is importance! Some paper may in query result only when you given
        explicit publication title.
        """
        self.query_ = query
        self.start_year_ = int(start_year)
        self.end_year_ = int(end_year)
        self.article_type_ = article_type
        self.subject_areas_ = subject_areas
        self.publication_title_ = publication_title
        self.agent = WebVPNAgent()

    @classmethod
    def from_url(cls, url):
        scheme, domain, path, query, _ = urlparse.urlsplit(url)
        query_set = query_decode(query, unquote=True)
        if "date" not in query_set:
            raise ValueError("`url` must have `date` condition. (customer year range)")
        if "qs" not in query_set:
            raise ValueError("`url` must have `qs` condition. (search condition)")
        query = query_set["qs"]
        start_year, end_year = query_set["date"].split("-")
        subject_areas = query_set.get("subjectAreas", None)
        article_type = query_set.get("articleType", None)
        publication_title = query_set.get("publicationTitle", None)
        return cls(query=query, start_year=start_year, end_year=end_year, subject_areas=subject_areas,
                   article_type=article_type, publication_title=publication_title)

    def _make_url(self):
        queries = {"qs": self.query_, "date": "%s-%s" % (self.start_year_, self.end_year_)}
        if self.subject_areas_:
            queries["subjectAreas"] = self.subject_areas_
        if self.article_type_:
            queries["articalType"] = self.article_type_
        if self.publication_title_:
            queries["publicationTitle"] = self.publication_title_
        payload = urlparse.urlencode(queries)
        return "https://www.sciencedirect.com/search/api?" + payload

    def _make_url_format(self):
        return self._make_url() + "&years={years}&show=100&offset={offset}"

    def _download_single_list(self, url, years, offset, show=100):
        response = self.agent.get(url)
        data = response.json()["searchResults"]
        data_columns = {
            "doi": "doi", "openAccess": "open_access", "title": "title",
            "publicationDate": "publication_date", "pii": "pii"
        }

        def make_dict(i, data_columns):
            d = {"years": years, "offset": offset, "show": show}
            for org_key, your_key in data_columns.items():
                if org_key == "title":
                    sel = etree.HTML(text=i[org_key])
                    d[your_key] = sel.xpath("string(.)")
                else:
                    d[your_key] = i[org_key]
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
        key = ""
        while 1:
            if idx == len(years):
                break
            data = years[idx]
            key = data["key"]
            count = data["value"]
            if count > 1000:
                warnings.warn("count greater than 1000, got %s" % count)
                conditions.append((key, count))
                idx += 1
                continue
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
        url_format = self._make_url_format()
        datas = []
        for i in range(max(9, int(math.ceil(paper_count * 1. / 100)))):
            offset = i * show
            url = url_format.format(years=years, offset=offset)
            data = self._download_single_list(url, years, offset, show)
            datas.extend(data)
        return datas

    def download(self):
        """Download paper list with conditions

        :return: list. list of dict of paper info.
        """
        # Publication title 应该单独考虑 # journal title and year range is recommended
        total_count, years, article_types, publication_titles = self._get_total_amount(self._make_url())
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
        sel = etree.HTML(text=response.text)
        journal = sel.xpath('//a[@class="publication-title-link"]/text()')[0]
        abstract = sel.xpath('//h2[contains(., "Abstract")]/following-sibling::div/p/text()')[0]
        keywords = sel.xpath('//div[@class="keyword"]/span/text()')
        data = {"journal": journal, "abstract": abstract, "keywords": keywords}
        return data


if __name__ == '__main__':
    url = 'https://www.sciencedirect.com/search?qs=%28%22trader%22%20OR%20%22human%22%20OR%20%22player%22%20OR%20%22avatar%22%29%20AND%20%28%22algorithm%22%20OR%20%22machine%22%20OR%20%22agent%22%20OR%20%22computer%22%29%20AND%20%28%22competition%22%29&date=2010-2021&lastSelectedFacet=articleTypes&subjectAreas=1700&articleTypes=FLA'
    dss_list_downloader = DSSPaperListDownloader.from_url(url)
    print(dss_list_downloader._make_url_format())
    print(dss_list_downloader.download())
