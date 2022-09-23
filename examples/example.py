#! python
# -*- coding: utf-8 -*-

"""
@Py-V  : 3
@File  : example.py
@Author: _
@Date  : 2020/4/21 18:49
@Ide   : PyCharm
@Desc  : 请求库测试...
"""
import logging
import threading
import aiohttp
from multi_process_asyncio.pool import Pool

logging.basicConfig(level=logging.INFO)


async def work(item):
    # 声明一个支持异步的上下文管理器
    async with aiohttp.ClientSession() as session:
        response = await session.get('https://www.baidu.com')
        text = await response.text()
        return item, text


def send_task(_pool, tasks):
    for task in tasks:
        _pool.submit(task)
    _pool.input_over()


if __name__ == '__main__':
    pool = Pool(work)
    pool.start()
    se = threading.Thread(target=send_task, args=(list(range(10000)), ))
    for i, w in pool.iter():
        print(i, len(w))
    se.join()

