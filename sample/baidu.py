#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sample.base_spider import BaseSpider


class Spider(BaseSpider):
    name = "百度"
    encoding = "utf-8"
    concurrent_limit = 100
    RETRY_TIME_DELAY = 0.01
    MAX_RETRY_COUNT = 5

    msgs = [
        "https://www.baidu.com/s" for i in range(100)
    ]

    async def start_request(self, msg):
        url = msg
        resp = await self.aio_request(
            url,
            auto_proxy=False,  # 自动添加代理
            auto_ua=False,  # 自动添加请求头
            follow_redirects=True,  # 重定向
            params={
                "wd": "你好"
            }
        )
        await self.logger.info(resp.code)


if __name__ == '__main__':
    spider = Spider()
    spider.run()
