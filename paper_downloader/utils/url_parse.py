# -*- coding: utf-8 -*-
"""
create on 2021-01-10 15:25
author @66492
"""
from urllib import parse as urlparse


def query_decode(query, unquote=True):
    def _split(query, unquote=True):
        key, val = query.split("=")
        if unquote:
            return urlparse.unquote(key), urlparse.unquote(val)
        return key, val

    queries = {}
    for q in query.split("&"):
        key, val = _split(q, unquote)
        queries[key] = val
    return queries
