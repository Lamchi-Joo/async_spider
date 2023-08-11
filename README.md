# async_spider

## ·异步采集小小小框架，项目使用Python3.7.5
## · 开始之前

1.**fork** 本仓库，然后clone你fork的仓库到你的本地：
```shell
git clone git@github.com:Lamchi-Joo/async_spider.git
```
2.拉取至本地后，创建python的虚拟环境：
```shell
virtualenv --no-site-packages venv
source venv/bin/activate
```
3.进入项目后，在项目根目录使用以下命令安装第三方依赖包
```shell
python -m pip install -r requirements.txt
```

## · demo

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from async_spider.spider import BaseSpider


class Spider(BaseSpider):
    name = "百度"
    encoding = "utf-8"
    concurrent_limit = 100
    RETRY_TIME_DELAY = 0.01
    MAX_RETRY_COUNT = 2

    urls = [
        "https://baidu.com" for i in range(100)
    ]

    async def start_request(self, url):
        resp = await self.aio_request(
            url,
            auto_proxy=False,  # 自动添加代理
            auto_ua=False,  # 自动更换请求头User-Agent
            follow_redirects=True  # 重定向
        )
        await self.logger.info(resp.code)
        text = self.decode_body(resp)
        print(text)


if __name__ == '__main__':
    spider = Spider()
    spider.run()

```

## · 框架特性

高性能，高并发，得益于Python对协程的支持：

* 完全异步
* 随机tls指纹
* 可使用布隆过滤器进行去重
* 可控的并发量
* 每消耗一个任务会立即开启新的任务
* 使用pycurl进行http连接，速度更快
* 异步日志打印，提升速度
* 请求重试装饰器，老板再也不用担心我丢数据啦
* 使用生成器以及队列进行任务的添加和提取，减少下一页递归时的内存占用（大规模采集可考虑替换为redis队列）

## · 注意：aiologger暂不支持windows，windows下开发可以把aiologger替换为loguru

## · 有任何使用问题联系
```shell
QQ: 11788683（备注来意）
```
