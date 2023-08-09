#! python
# -*- coding: utf-8 -*-

"""
@Py-V  : 3
@File  : example_aiohttp.py
@Author: _
@Date  : 2020/4/21 18:49
@Ide   : PyCharm
@Desc  : 请求库测试...
"""
import logging
import threading
import time

import aiohttp
from multi_process_asyncio.pool import Pool


async def aiohttp_client():
    # 进程隔离， 每个进程运行一次
    # 声明一个支持异步的上下文管理器
    timeout = 100
    return aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(
            ssl=False,
            force_close=True,
            enable_cleanup_closed=True,
        ),
        timeout=aiohttp.ClientTimeout(
            total=timeout,
            connect=timeout,
            sock_read=timeout,
            sock_connect=timeout,
        )
    )


async def example_aiohttp_work(client: aiohttp.ClientSession, task_num):
    # 声明一个支持异步的上下文管理器
    response = await client.get('https://www.baidu.com')
    text = await response.text()
    return task_num, text


def example_aiohttp_send(_pool: Pool, tasks):
    for task_num in tasks:
        _pool.submit(example_aiohttp_work, task_num)
    _pool.input_over()


def example_aiohttp_save(_pool):
    for i, w in _pool.iter():
        print(i, len(w))


if __name__ == '__main__':
    stime = time.perf_counter()
    logging.basicConfig(level=logging.INFO)

    pool = Pool(async_client=aiohttp_client, asyncio_debug=True)
    sd = threading.Thread(target=example_aiohttp_send, args=(pool, list(range(1000)),))
    sv = threading.Thread(target=example_aiohttp_save, args=(pool,))

    sv.start()
    sd.start()
    pool.start()

    sd.join()
    sv.join()

    print("time:", time.perf_counter() - stime)