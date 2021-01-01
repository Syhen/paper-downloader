# -*- coding: utf-8 -*-
"""
create on 2020-12-30 11:21
author @66492
"""
from binascii import hexlify, unhexlify
from urllib import parse as urlparse

from Crypto.Cipher import AES


class AESEncryptor(object):
    def __init__(self, key=b'wrdvpnisthebest!', iv=b'wrdvpnisthebest!'):
        self.key_ = key
        self.iv_ = iv

    def encrypt(self, text: str, size=128):
        text = text.encode("utf8") if isinstance(text, str) else text
        cfb_cipher_encrypt = AES.new(self.key_, AES.MODE_CFB, self.iv_, segment_size=size)
        cipher_text = hexlify(cfb_cipher_encrypt.encrypt(text)).decode()
        return cipher_text

    def decrypt(self, cipher_text: str, size=128):
        cipher_text = cipher_text.encode('utf-8') if isinstance(cipher_text, str) else cipher_text
        message = unhexlify(cipher_text)
        cfb_cipher_decrypt = AES.new(self.key_, AES.MODE_CFB, self.iv_, segment_size=size)
        text = cfb_cipher_decrypt.decrypt(message).decode('utf-8')
        return text


class WebVPNEncoder(object):
    def __init__(self, institution='webvpn.swufe.edu.cn', key=b'wrdvpnisthebest!', iv=b'wrdvpnisthebest!'):
        self.institution_ = institution
        self.encryptor_ = AESEncryptor(key, iv)
        self.hex_key_ = hexlify(iv).decode('utf-8')

    def encode(self, url):
        scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
        cph = self.encryptor_.encrypt(netloc)
        fold = path if not query else '%s?%s' % (path, query)
        key = hexlify(self.encryptor_.iv_).decode('utf-8')
        return urlparse.urljoin('https://%s' % self.institution_, '%s/%s/%s' % (scheme, key + cph, fold))

    def decode(self, url):
        parts = url.split('/')
        scheme = parts[3]
        key_cph = parts[4]

        if key_cph[:16] == hexlify(self.encryptor_.iv_).decode('utf-8'):
            return None
        netloc = self.encryptor_.decrypt(key_cph[32:64])
        fold = '/'.join(parts[5:])
        return scheme + "://" + netloc + '/' + fold


class UrlEncoder(object):
    def __init__(self, **kwargs):
        pass


if __name__ == '__main__':
    import time

    webvpn_encoder = WebVPNEncoder()
    # https://webvpn.swufe.edu.cn/http/77726476706e69737468656265737421e1fe4a9d297e6b41680199e29b5a2e/

    # url = 'https://kns.cnki.net/KCMS/detail/detail.aspx?dbcode=CJFQ&dbname=CJFD2007&filename=JEXK200702000&uid=WEEvREcwSlJHSldRa1FhcTdnTnhXY20wTWhLQWVGdmJFOTcvMFFDWDBycz0=$9A4hF_YAuvQ5obgVAqNKPCYcEjKensW4IQMovwHtwkF4VYPoHbKxJw!!&v=MTYzNjU3cWZaT2RuRkNuaFZMN0tMeWpUWmJHNEh0Yk1yWTlGWklSOGVYMUx1eFlTN0RoMVQzcVRyV00xRnJDVVI='
    url = "https://www.sciencedirect.com/science/article/pii/S0167923620302049/pdfft?md5=3f6a55a0b6b2e0ac7d3d35729cb21672&pid=1-s2.0-S0167923620302049-main.pdf"
    print('From ordinary url: \n' + webvpn_encoder.encode(url))
    url = webvpn_encoder.encode(url) + "?wrdrecordvisit=%s" % (int(time.time() * 1000))
    print(url)
    VPNUrl = 'https://webvpn.dlut.edu.cn/https/77726476706e69737468656265737421fbf952d2243e635930068cb8/KCMS/detail/detail.aspx?dbcode=CJFQ&dbname=CJFD2007&filename=JEXK200702000&uid=WEEvREcwSlJHSldRa1FhcTdnTnhXY20wTWhLQWVGdmJFOTcvMFFDWDBycz0=$9A4hF_YAuvQ5obgVAqNKPCYcEjKensW4IQMovwHtwkF4VYPoHbKxJw!!&v=MTYzNjU3cWZaT2RuRkNuaFZMN0tMeWpUWmJHNEh0Yk1yWTlGWklSOGVYMUx1eFlTN0RoMVQzcVRyV00xRnJDVVI='
    print('\nFrom webVPN url: \n' + webvpn_encoder.decode(VPNUrl))
    print(webvpn_encoder.encode('https://www.sciencedirect.com/science/article/pii/S0167923620302049/pdfft?md5=3f6a55a0b6b2e0ac7d3d35729cb21672&pid=1-s2.0-S0167923620302049-main.pdf'))
