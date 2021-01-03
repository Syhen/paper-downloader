# -*- coding: utf-8 -*-
"""
create on 2021-01-03 21:04
author @66492
"""
import hashlib


def md5(text: str, size=32):
    return hashlib.md5(text.encode("utf8")).hexdigest()[:size]


if __name__ == '__main__':
    print(md5("jiewa"))
