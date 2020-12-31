# -*- coding: utf-8 -*-
"""
create on 2020-12-31 15:22
author @66492
"""
from paper_downloader.settings import settings, default_settings


class Settings(object):
    def __init__(self, settings: dict):
        self._settings = settings

    @classmethod
    def from_objs(cls, settings):
        _settings = {}
        for name in dir(settings):
            if name.startswith("_"):
                continue
            _settings[name] = getattr(settings, name)
            setattr(cls, name, getattr(settings, name))
        return cls(_settings)

    def get(self, name, default=None):
        return self._settings.get(name, default)

    def get_int(self, name, default=0):
        val = self._settings.get(name, default)
        try:
            return int(val)
        except ValueError as e:
            raise e


settings = Settings.from_objs(settings)
