# -*- coding: utf-8 -*-
"""
create on 2021-01-01 13:12
author @66492
"""
from urllib import parse as urlparse

from lxml import etree

from paper_downloader import exceptions
from paper_downloader.agent.webvpn import WebVPNAgent
from paper_downloader.downloader.base import BaseDownloader
from paper_downloader.utils.encryto.aes import WebVPNEncoder


class TaylorDownloader(BaseDownloader):
    domain = "https://webvpn.swufe.edu.cn/"

    def __init__(self, agent_cls=WebVPNAgent, encoder_cls=WebVPNEncoder, dir="C:/Users/66492/Desktop"):
        super(TaylorDownloader, self).__init__(agent_cls=agent_cls, encoder_cls=encoder_cls, dir=dir)
        if self.domain is None:
            raise ValueError("please set `domain` when creating Downloader class.")

    def _get_pdf_url(self, url):
        response = self.agent.get(self.encoder.encode(url))
        sel = etree.HTML(text=response.text)
        pdf_name_element = sel.xpath('//span[@class="NLM_article-title hlFld-title"]/text()')
        if not pdf_name_element:
            raise exceptions.AccessDeny("your vpn were logged out, please log in and try again.")
        pdf_name = pdf_name_element[0]
        pdf_url = sel.xpath('//a[@class="show-pdf"]/@href')[0]
        pdf_url = self.encoder.encode(urlparse.urljoin(self.domain, pdf_url))
        return pdf_url, pdf_name

    def download(self, url: str, filename=None):
        self.agent.load_cookies()
        pdf_url, pdf_name = self._get_pdf_url(url)
        filename = filename if filename else pdf_name
        self._download_pdf(pdf_url, filename)
        return pdf_url


if __name__ == '__main__':
    taylor_downloader = TaylorDownloader()
    print(taylor_downloader.download("https://doi.org/10.1080/07421222.2017.1334494"))
