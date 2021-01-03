# -*- coding: utf-8 -*-
"""
create on 2021-01-01 15:42
author @66492
"""
import json
from urllib import parse as urlparse

from lxml import etree

from paper_downloader import exceptions
from paper_downloader.agent.webvpn import WebVPNAgent
from paper_downloader.downloader.base import BaseDownloader
from paper_downloader.utils.encryto.aes import WebVPNEncoder


class SciHubDownloader(BaseDownloader):
    domain = "https://sci-hub.se/"

    def __init__(self, agent_cls=WebVPNAgent, encoder_cls=WebVPNEncoder, dir="C:/Users/66492/Desktop"):
        super(SciHubDownloader, self).__init__(agent_cls=agent_cls, encoder_cls=encoder_cls, dir=dir)
        if self.domain is None:
            raise ValueError("please set `domain` when creating Downloader class.")

    def _get_pdf_url(self, url):
        response = self.agent.get(url)
        sel = etree.HTML(text=response.text)
        filename = sel.xpath('//div[@id="citation"]/text()')[0]
        pdf_url = urlparse.urljoin(self.domain, sel.xpath('//div[@id="article"]/iframe/@src')[0])
        return pdf_url, filename

    def download(self, doi: str, filename=None, **kwargs):
        """Download pdf file with given url

        :param doi: str. paper doi.
        :param filename: str or None. default None. If None, paper title will be used.
        :return: str. if succeed, return url of pdf file. else, raise exceptions.
        """
        url = urlparse.urljoin(self.domain, doi)
        pdf_url, pdf_name = self._get_pdf_url(url)
        filename = filename if filename else pdf_name
        self._download_pdf(pdf_url, filename, **kwargs)
        return pdf_url


if __name__ == '__main__':
    scihub_downloader = SciHubDownloader()
    print(scihub_downloader.download("10.1016/j.dss.2020.113449", filename=None, timeout=30))
