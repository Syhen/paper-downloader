# -*- coding: utf-8 -*-
"""
create on 2020-12-29 23:26
author @66492
"""
import pickle
import requests
from lxml import etree

from paper_downloader.settings import settings, default_settings


class WebVPNAgent(object):
    def __init__(self, school="swufe"):
        self.school_ = school
        self.login_url = "https://webvpn.%s.edu.cn/login" % school
        self.login_form_url = "https://webvpn.%s.edu.cn/do-login" % school
        self.headers = {
            "User-Agent": settings.get("USER_AGENT"),
        }
        self.cookies_ = None

    def _collect_info(self):
        response = requests.get(self.login_url, headers=self.headers)
        sel = etree.HTML(text=response.text)
        captcha_id = sel.xpath('//input[@name="captcha_id"]/@value')[0]
        return {"captcha_id": captcha_id}

    def post(self, url, data, headers=None, cookies=None, **kwargs):
        headers = headers or self.headers
        cookies = cookies or self.cookies_
        response = requests.post(url, data, headers=headers, cookies=cookies, **kwargs)
        return response

    def get(self, url, params=None, headers=None, cookies=None, **kwargs):
        headers = headers or self.headers
        cookies = cookies or self.cookies_
        response = requests.get(url, params=params, headers=headers, cookies=cookies, **kwargs)
        return response

    def login(self, username, password):
        body = {
            "auth_type": "local",
            "username": username,
            "sms_code": "",
            "password": password,
            "captcha": "",
            "needCaptcha": "false",
            "captcha_id": ""
        }
        body.update(self._collect_info())
        self.before_login()
        response = self.post(self.login_form_url, data=body)
        self.after_login(response)
        return

    def _get_cookie_filename(self):
        cookie_file_path = settings.get("COOKIE_FILE_PATH", default_settings.COOKIE_FILE_PATH)
        cookie_filename = settings.get("COOKIE_FILENAME", default_settings.COOKIE_FILENAME)
        cookie_filename = os.path.join(cookie_file_path, cookie_filename)
        if not os.path.exists(cookie_file_path):
            os.makedirs(cookie_file_path)
        return cookie_filename

    def test_cookie(self, username, headers=None, cookies=None, **kwargs):
        headers = headers or self.headers
        cookies = cookies or self.cookies_
        response = self.get("https://webvpn.%s.edu.cn/" % self.school_, headers=headers, cookies=cookies, **kwargs)
        print(response.request.headers)
        return username in response.text

    def load_cookies(self):
        cookie_filename = self._get_cookie_filename()
        try:
            with open(cookie_filename, "rb") as f:
                cookie, cookie_in_headers = pickle.load(f)
        except FileNotFoundError:
            return
        if self.cookies_ is None:
            self.cookies_ = cookie
        self.headers["Cookie"] = cookie_in_headers
        self.cookies_.update(cookie)

    def before_login(self):
        self.load_cookies()

    def after_login(self, response):
        cookie_filename = self._get_cookie_filename()
        cookie_in_headers = response.headers.get("Set-Cookie", "")
        with open(cookie_filename, "wb") as f:
            pickle.dump((response.cookies, cookie_in_headers), f)


if __name__ == '__main__':
    import os

    username = os.environ.get("WEBVPN_USERNAME")
    password = os.environ.get("WEBVPN_PASSWORD")
    webvpn_agent = WebVPNAgent()
    webvpn_agent.load_cookies()
    cookie_is_ok = webvpn_agent.test_cookie(username)
    print("cookie is ok:", cookie_is_ok)
    if not cookie_is_ok:
        webvpn_agent.login(username, password)
