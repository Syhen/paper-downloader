# -*- coding: utf-8 -*-
"""
create on 2020-12-29 17:18
author @66492
"""
import json
from urllib import parse as urlparse

from lxml import etree

from paper_downloader import exceptions
from paper_downloader.downloader.base import BaseDownloader


class DSSDownloader(BaseDownloader):
    domain = "https://www.sciencedirect.com/"

    def __init__(self, dir="C:/Users/66492/Desktop"):
        super(DSSDownloader, self).__init__(dir=dir)
        if self.domain is None:
            raise ValueError("please set `domain` when creating Downloader class.")

    def _extract_redirect_url(self, text):
        sel = etree.HTML(text=text)
        redirect_url = sel.xpath('//input[@name="redirectURL"]/@value')[0]
        return urlparse.unquote(redirect_url)

    def _extract_pdf_url(self, redirect_url):
        text = self.agent.get(redirect_url).text
        data = json.loads(etree.HTML(text=text).xpath('//script[contains(.,"abstracts")]/text()')[0])
        article_data = data["article"]
        if "pdfDownload" not in article_data:
            raise exceptions.AccessDeny("your vpn were logged out, please log in and try again.")
        pdf_link = urlparse.urljoin(self.domain, article_data["pdfDownload"]["linkToPdf"])
        filename = data["article"]["titleString"]
        pdf_url = etree.HTML(self.agent.get(pdf_link).text).xpath('//a/@href')[0]
        return pdf_url, filename

    def download(self, url: str, filename=None):
        """Download pdf file with given url

        :param url: str. dss pdf url, s.t. https://doi.org/10.1016/j.dss.2018.05.006
        :param filename: str or None. default None. If None, paper title will be used.
        :return: str. if succeed, return url of pdf file. else, raise exceptions.
        """
        redirect_url = self._extract_redirect_url(self.agent.get(url).text)
        pdf_url, pdf_name = self._extract_pdf_url(redirect_url)
        filename = filename if filename else pdf_name
        self._download_pdf(pdf_url, filename)
        return pdf_url


if __name__ == '__main__':
    dss_downloader = DSSDownloader()
    print(dss_downloader.download("https://doi.org/10.1016/j.dss.2009.05.016", filename=None))
