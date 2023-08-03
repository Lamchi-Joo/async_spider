#!/usr/bin/env python
# -*- coding:utf-8 -*-

from tornado.httpclient import AsyncHTTPClient

AsyncHTTPClient.configure(
    'async_spider.request_wrapper.curl_async_http_client.CurlAsyncHTTPClient'
)


class RequestWrapper(object):

    def __init__(self):
        pass

    @staticmethod
    async def fetch(*args, **kwargs):
        async_http_client = AsyncHTTPClient(force_instance=True)
        try:
            res = await async_http_client.fetch(*args, **kwargs)
            async_http_client.close()
        except Exception as e:
            async_http_client.close()
            raise e
        return res
