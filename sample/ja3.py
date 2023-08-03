#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    ja3.py
    ~~~~~~~~~~~

    :author: Lamchi
    :copyright: (c) 2023, qizhidao
    :date created: 2023-08-03
    :python version: 3.7.3
"""
from async_spider.spider import BaseSpider


class Spider(BaseSpider):
    name = "ja3"
    encoding = "utf-8"
    RETRY_TIME_DELAY = 0.01
    MAX_RETRY_COUNT = 5
    concurrent_limit = 100
    headers = {
        "Accept": "text/html,application/xhtml+xml,"
                  "application/xml;q=0.9,image/avif,image/webp,"
                  "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Referer": "http://www.hyffw.com/company/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
    }

    msgs = ["https://tls.browserleaks.com/json" for i in range(20)]

    async def start_request(self, msg):
        await self.logger.info(f"[RECEIVED] {msg}")
        resp = await self.aio_request(msg, headers=self.headers, follow_redirects=False, auto_proxy=False)
        if resp and resp.code == 200 and resp.body:
            text = self.decode_body(resp)
            if not text:
                return
            print(text)
            # print(resp.code)
        else:
            await self.logger.info(f"[DROP][LIST] {msg}")


if __name__ == '__main__':
    s = Spider()
    s.run()
