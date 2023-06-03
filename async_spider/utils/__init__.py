#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import asyncio
from functools import wraps

import aiohttp
import aiohttp.client_exceptions
from tornado.httpclient import HTTPError


def request_retry():
    """
    重试装饰器
    """

    def wrap(func):
        @wraps(func)
        async def inner(self, *args, **kwargs):
            retry_count = 0
            max_retry_count = self.MAX_RETRY_COUNT
            retry_time_delay = self.RETRY_TIME_DELAY
            if 'url' in kwargs:
                url = kwargs.get('url')
            else:
                url = args[0]
            if not url:
                raise Exception('url is None')
            if not (isinstance(max_retry_count, int) and max_retry_count >= 0):
                raise Exception('max_retry_count must be integer and greater or equal to 0')
            while True:
                if retry_count > max_retry_count:
                    return
                if retry_count > 0:
                    await self.logger.info(f'[RETRY] retry_count: {retry_count}, url: {url}')
                try:
                    result = await func(self, *args, **kwargs)
                except aiohttp.client_exceptions.ClientConnectorError:
                    # 处理ip代理挂了的情况
                    retry_count += 1
                    await asyncio.sleep(300)
                except HTTPError as e:
                    if e.response:
                        if e.response.code == 404:
                            # 404 not found, return immediately
                            return
                        else:
                            retry_count += 1
                            if retry_time_delay:
                                await asyncio.sleep(retry_time_delay)
                    else:
                        retry_count += 1
                        if retry_time_delay:
                            await asyncio.sleep(retry_time_delay)
                except:
                    retry_count += 1
                    if retry_time_delay:
                        await asyncio.sleep(retry_time_delay)
                else:
                    return result

        return inner

    return wrap


async def get_proxies():
    # 使用aiohttp来请求代理，能加快速度，aiohttp暂时不支持https代理，所以请求基类没有使用aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(f'代理地址') as response:
            proxy = await response.text(encoding='utf-8')
            match_auth = re.match(
                r'([^:/]*):([^:/]*)@([^:/]*):(\d+)$', proxy
            )
            # tornado CurlAsyncHTTPClient代理格式，固定的
            match_host = re.match(r'([^:/]*):(\d+)$', proxy)
            if match_auth:
                return dict(
                    proxy_username=match_auth.group(1),
                    proxy_password=match_auth.group(2),
                    proxy_host=match_auth.group(3),
                    proxy_port=int(match_auth.group(4)),
                )
            elif match_host:
                return dict(
                    proxy_host=match_host.group(1),
                    proxy_port=int(match_host.group(2)),
                )


def main():
    return asyncio.run(get_proxies())


if __name__ == '__main__':
    print(main())
