# -*- coding: utf-8 -*-
"""
create on 2020-12-29 17:16
author @66492
"""
import os

import requests

from paper_downloader.agent.webvpn import WebVPNAgent
from paper_downloader.settings import settings, default_settings


class BaseDownloader(object):
    domain = None

    def __init__(self, agent_cls=WebVPNAgent, dir="/Users/66492/Desktop"):
        self.dir_ = dir
        self.headers = {
            "user-agent": settings.get("USER_AGENT", default_settings.USER_AGENT),
        }
        self.agent = WebVPNAgent(school=settings.get("SCHOOL", default_settings.SCHOOL))

    def download(self, url):
        raise NotImplemented()

    def _complete_filename(self, filename):
        if "/" in filename:
            return filename
        if ".pdf" not in filename:
            return os.path.join(self.dir_, filename + ".pdf")
        return os.path.join(self.dir_, filename)

    def _download_pdf(self, pdf_url, filename):
        filename = self._complete_filename(filename)
        with open(filename, "wb") as f:
            f.write(requests.get(pdf_url, headers=self.headers).content)


if __name__ == '__main__':
    pdf_url = "https://www.sciencedirect.com/science/article/pii/S0167923618300861/pdfft?md5=26b93d5a4e15fe884ffc0e8767977a1e&pid=1-s2.0-S0167923618300861-main.pdf"
    downloader = BaseDownloader()
    response = requests.get(pdf_url, headers=downloader.headers)
    downloader._download_pdf(pdf_url, "C:/Users/66492/Desktop/test_heyao.pdf")
