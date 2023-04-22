#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import datetime
import os
import sys
from os import makedirs
from os.path import dirname, exists, abspath

from aiologger import Logger
from aiologger.formatters.base import Formatter
from aiologger.handlers.files import AsyncFileHandler
from aiologger.handlers.streams import AsyncStreamHandler

loggers = {}

LOG_ENABLED = True  # 是否开启日志
LOG_TO_CONSOLE = True  # 是否输出到控制台
LOG_TO_FILE = True  # 是否输出到文件

LOG_DIR = os.path.join(dirname(abspath(__file__)), 'logs')
LOG_LEVEL = 'DEBUG'  # 日志级别
LOG_FORMAT = '[%(asctime)s][%(name)s] - [%(levelname)s]  - %(message)s'  # 每条日志输出格式


def get_logger(name=None, debug=False) -> Logger:
    """
    get logger by name
    :param name: name of logger
    :param debug: debug true or false
    :return: logger
    """
    global loggers

    if not name:
        raise Exception('logger name is None')

    level = 'DEBUG' if debug else 'INFO'
    logger = Logger(name=name, level=level)
    if loggers.get(name):
        return loggers[name]

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    file_name = name + '-' + today + '.log'
    log_path = os.path.join(LOG_DIR, file_name)

    # 输出到控制台
    if not logger.handlers:
        formatter = Formatter(LOG_FORMAT)
        if LOG_ENABLED and LOG_TO_CONSOLE:
            stream_handler = AsyncStreamHandler(sys.stdout, level=LOG_LEVEL, formatter=formatter)
            logger.add_handler(stream_handler)

        # 输出到文件
        if LOG_ENABLED and LOG_TO_FILE:
            # 如果路径不存在，创建日志文件文件夹
            log_dir = dirname(log_path)
            if not exists(log_dir):
                makedirs(log_dir)
            # 添加 FileHandler
            file_handler = AsyncFileHandler(filename=log_path, encoding='utf-8', mode='a')
            file_handler.formatter = formatter
            logger.add_handler(file_handler)

    # 保存到全局 loggers
    loggers[name] = logger
    return loggers[name]


async def main():
    logger = get_logger('test_logger')
    log_list = []
    for i in range(100):
        log_list.append(
            logger.info(f'hello error {i}')
        )
    await asyncio.gather(*log_list)

    await logger.shutdown()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
