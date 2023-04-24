#!/usr/bin/env python
# -*- coding:utf-8 -*-

from .curl_async_http_client import CurlAsyncHTTPClient


class RequestWrapper(object):

    def __init__(self):
        pass

    @staticmethod
    async def fetch(*args, **kwargs):
        fetcher = CurlAsyncHTTPClient(force_instance=True)
        try:
            res = await fetcher.fetch(*args, **kwargs)
            fetcher.close()
        except Exception as e:
            fetcher.close()
            raise e
        return res
