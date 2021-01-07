# -*- coding: utf-8 -*-
"""
create on 2020-12-29 17:16
author @66492
"""
import math
import os

import requests
from tqdm import tqdm

from paper_downloader.agent.webvpn import WebVPNAgent
from paper_downloader.settings import settings, default_settings
from paper_downloader.utils.encryto.aes import WebVPNEncoder
from paper_downloader.utils.encryto.md5 import md5


class BaseDownloader(object):
    domain = None

    def __init__(self, agent_cls=WebVPNAgent, encoder_cls=WebVPNEncoder, dir="/Users/66492/Desktop"):
        self.dir_ = dir
        self.headers = {
            "user-agent": settings.get("USER_AGENT", default_settings.USER_AGENT),
        }
        self.agent = agent_cls(school=settings.get("SCHOOL", default_settings.SCHOOL))
        self.encoder = encoder_cls()

    def download(self, url: str, filename=None):
        raise NotImplemented()

    def _complete_filename(self, filename):
        def filename_filter(filename):
            filters = ["\\", "/", ":", "*", "?", "<", ">", "|", '"']
            for filter_str in filters:
                if filter_str in filename:
                    filename = filename.replace(filter_str, "-")
            return filename
        if "/" in filename:
            return filename
        if ".pdf" not in filename:
            filename += ".pdf"
        filename = filename_filter(filename)
        return os.path.join(self.dir_, filename)

    def _get_file_size(self, filename):
        if os.path.exists(filename):
            return os.path.getsize(filename)
        return 0

    def _get_total_file_size(self, pdf_url, response=None):
        filename = ".%s.tmp" % md5(pdf_url, size=16)
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return int(f.read())
        if response is None:
            return 0
        file_size = response.headers.get("Content-Length", None)
        file_size = None if file_size is None else int(file_size)
        with open(filename, "w") as f:
            f.write("%s" % file_size)
        return file_size

    def _download_chuck(self, pdf_url, filename, chunk_size=50 * 1024, **download_kwargs):
        self.agent.headers["Range"] = "bytes=%d-" % self._get_file_size(filename)
        response = self.agent.get(pdf_url, stream=True, verify=True, **download_kwargs)
        file_size = self._get_total_file_size(pdf_url, response)
        total_chunk = self._get_file_size(filename)
        total_iters = math.ceil((file_size - total_chunk) / chunk_size)
        with open(filename, "ab") as f:
            with tqdm(response.iter_content(chunk_size=chunk_size), total=total_iters) as t:
                for chunk in t:
                    f.write(chunk)
                    total_chunk += len(chunk)
                    f.flush()
        return total_chunk

    def _download_pdf(self, pdf_url, filename, chunk_size=50 * 1024, **kwargs):
        filename = self._complete_filename(filename)
        total_chunk, retry_times = self._get_file_size(filename), 0
        response = self.agent.get(pdf_url, stream=True, verify=True, **kwargs)
        file_size = self._get_total_file_size(pdf_url, response)
        print("downloaded:", total_chunk, ", total size:", file_size)
        do_not_retry = bool(file_size is None)
        while 1:
            total_chunk = self._get_file_size(filename)
            try:
                self._download_chuck(pdf_url, filename=filename, chunk_size=chunk_size, **kwargs)
            except requests.exceptions.RequestException:
                continue
            if total_chunk >= file_size or do_not_retry:
                break
            retry_times += 1
        print("download finished. downloaded:", total_chunk, ", total:", file_size)
        return total_chunk == file_size


if __name__ == '__main__':
    pdf_url = "https://www.sciencedirect.com/science/article/pii/S0167923618300861/pdfft?md5=26b93d5a4e15fe884ffc0e8767977a1e&pid=1-s2.0-S0167923618300861-main.pdf"
    downloader = BaseDownloader()
    response = requests.get(pdf_url, headers=downloader.headers)
    downloader._download_pdf(pdf_url, "C:/Users/66492/Desktop/test_heyao.pdf")
