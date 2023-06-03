#!/usr/bin/env python
# -*- coding:utf-8 -*-

from .curl_async_http_client import CurlAsyncHTTPClient


class RequestWrapper(object):

    def __init__(self):
        pass

    @staticmethod
    async def fetch(*args, **kwargs):
        async_http_client = CurlAsyncHTTPClient(force_instance=True)
        try:
            res = await async_http_client.fetch(*args, **kwargs)
            async_http_client.close()
        except Exception as e:
            async_http_client.close()
            raise e
        return res
