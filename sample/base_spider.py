#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
from copy import deepcopy
import time
import traceback
from typing import Optional, Union
import warnings

from tornado.httpclient import HTTPResponse
import cchardet as chardet
from tornado.httputil import url_concat
from fake_useragent import UserAgent

from aiologger_helper import get_logger
from bloom_filter_on_redis import RedisBloomFilter
from request import RequestWrapper
from util import request_retry, get_proxies

try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    warnings.filterwarnings('ignore')
except (ModuleNotFoundError, ImportError):
    pass


class BaseSpider(object):
    MAX_RETRY_COUNT = 5  # 重试次数
    RETRY_TIME_DELAY = 0  # 重试延迟
    concurrent_limit = 50  # 并发次数
    msgs = []  # url list or other keyword list
    name = ""
    encoding = "utf-8"  # 解码 HTTPResponse.body

    def __init__(self):

        self.logger = None
        self.semaphore = None
        self.db = None
        self.bf = None
        self.task_queue = None
        self.requester = RequestWrapper()
        self.fake_user_agent = UserAgent()
        assert self.name != "", "Spider`name is empty"

    @request_retry()
    async def aio_request(
            self,
            url: Optional[str] = None,
            **kwargs
    ) -> HTTPResponse:
        """
        :param url:
        :param kwargs: url,headers,data,params,etc,,
        """
        auto_proxy = kwargs.pop("auto_proxy", True)
        auto_ua = kwargs.pop("auto_ua", False)
        if 'params' in kwargs:
            url = url_concat(url, kwargs['params'])
            del kwargs['params']
        if 'request_timeout' not in kwargs:
            kwargs['request_timeout'] = 30
        if 'max_redirects' not in kwargs:
            kwargs['max_redirects'] = 3
        if 'data' in kwargs:
            kwargs['body'] = url_concat('?', kwargs['data'])[1:]
            del kwargs['data']
        if 'formdata' in kwargs:
            kwargs['body'] = url_concat('?', kwargs['formdata'])[1:]
            del kwargs['formdata']
        if 'connect_timeout' not in kwargs:
            kwargs['connect_timeout'] = 30
        if 'follow_redirects' not in kwargs:
            kwargs['follow_redirects'] = False
        if 'validate_cert' not in kwargs:
            kwargs['validate_cert'] = False
        if 'method' not in kwargs:
            kwargs['method'] = "GET"
        if 'headers' not in kwargs:
            kwargs['headers'] = {
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Cache-Control": "no-cache",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/111.0.0.0 Safari/537.36"
            }
        if auto_proxy:
            proxy = await get_proxies()
            kwargs.update(proxy)
        if auto_ua:
            headers = deepcopy(kwargs['headers'])
            headers['User-Agent'] = self.fake_user_agent.random
            kwargs['headers'] = headers
        response = await self.requester.fetch(url, **kwargs)
        return response

    async def create_task(self, msg: Optional[Union[str, int]] = None) -> None:
        """
        :param msg: url or other keyword
        :return:
        """
        async with self.semaphore:
            try:
                await self.start_request(msg)
            except:
                await self.logger.warning(traceback.format_exc())

    async def start_request(self, msg):
        raise NotImplementedError

    def msg_generator(self):
        """
        使用生成器来节省内存，如果大批量采集可以复写该函数，例如文件读写
        with open("*******", "r") as f:
            for i in f:
                yield i.strip()
        """
        for msg in self.msgs:
            yield msg

    async def start(self):
        """
        start running
        :return:
        """
        await self.init_session()
        await self.logger.info(f'{self.name} start running！！！')
        start_time = time.monotonic()

        msg_generator = self.msg_generator()
        while True:
            msgs = []
            q_size = self.concurrent_limit - self.task_queue.qsize()
            if q_size > 0:
                for i in range(q_size):
                    try:
                        msg = next(msg_generator)
                        self.task_queue.put_nowait(msg)
                    except StopIteration:
                        break

            for i in range(self.concurrent_limit):
                try:
                    msg = self.task_queue.get_nowait()
                    msgs.append(msg)
                except asyncio.queues.QueueEmpty:
                    break
            if not msgs:
                break
            coroutines = [asyncio.ensure_future(self.create_task(msg)) for msg in msgs]
            await asyncio.wait(coroutines)
        end_time = time.monotonic()
        elapsed_time = end_time - start_time
        elapsed_time_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        await self.logger.info(
            f'{self.name} finished, cost time: {elapsed_time_str}.'
        )
        await self.close()

    async def save_result(
            self,
            *args,
            **kwargs
    ):
        pass

    async def init_session(self):
        self.semaphore = asyncio.Semaphore(value=self.concurrent_limit)
        self.task_queue = asyncio.Queue()
        name = "debug_filter"
        self.bf = RedisBloomFilter(name=name)  # 布隆过滤器
        self.logger = get_logger(self.name)

    def run(self):
        """
        入口函数
        :return:
        """
        asyncio.run(self.start())

    def decode_body(self, response):
        """
        解码，采用cchardet来进行解码
        """
        try:
            text = response.body.decode(self.encoding)
        except UnicodeDecodeError:
            try:
                encodings = chardet.detect(response.body)
                if encodings:
                    encoding = encodings["encoding"]
                else:
                    return
                text = response.body.decode(encoding, 'ignore').encode('utf-8', 'ignore').decode()
            except:
                return
        return text

    async def close(self):
        """
        :return:
        """
        await self.logger.shutdown()
        await asyncio.sleep(0.05)  # 优雅的关闭退出

    def __del__(self):
        self.bf.__del__()
