#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import asyncio
from functools import wraps
from http.cookies import SimpleCookie
from urllib.parse import urljoin

import aiohttp
import aiohttp.client_exceptions
from tornado.httpclient import HTTPError


def request_retry():
    """
    重试装饰器
    """

    def wrap(func):
        @wraps(func)
        async def inner(self, url, **kwargs):
            retry_count = 0
            redirect_times = 0
            max_redirects = 5
            if kwargs.get("max_redirects"):
                max_redirects = kwargs["max_redirects"]
            follow_redirects = True
            if "follow_redirects" in kwargs:
                follow_redirects = kwargs["follow_redirects"]
            if 'headers' not in kwargs:
                kwargs['headers'] = {
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                    "Cache-Control": "no-cache",
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/111.0.0.0 Safari/537.36"
                }
            kwargs["follow_redirects"] = False
            cookiejar = None
            max_retry_count = self.MAX_RETRY_COUNT
            retry_time_delay = self.RETRY_TIME_DELAY
            if not url:
                raise Exception('url is None')
            await self.logger.info(f'[GET] url: {url}')
            while True:
                if retry_count > max_retry_count:
                    return
                try:
                    result = await func(self, url, **kwargs)
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
                            if 300 <= e.response.code < 400:
                                if follow_redirects and redirect_times <= max_redirects:
                                    redirect_times += 1
                                    location = e.response.headers.get(
                                        'Location', None
                                    )
                                    set_cookies = e.response.headers.get_list(
                                        'Set-Cookie'
                                    )
                                    if location:
                                        target_url = urljoin(
                                            url, location
                                        )
                                        if target_url:
                                            url = target_url
                                        else:
                                            url = location

                                    if cookiejar is None:
                                        cookiejar = SimpleCookie()

                                    cookiejar.load(
                                        kwargs["headers"].get('Cookie', '')
                                    )

                                    if set_cookies:
                                        for set_cookie in set_cookies:
                                            cookiejar.load(set_cookie)

                                    cookie = '; '.join(
                                        [
                                            key + '=' + morsel.value
                                            for key, morsel in cookiejar.items()
                                        ]
                                    )
                                    kwargs["headers"]['Cookie'] = cookie
                                else:
                                    return
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
