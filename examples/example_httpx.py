#! python
# -*- coding: utf-8 -*-

"""
@Py-V  : 3
@File  : example_httpx.py
@Author: _
@Date  : 2020/4/21 18:49
@Ide   : PyCharm
@Desc  : 请求库测试...
"""
import logging
import threading
import time

import httpx
from multi_process_asyncio.pool import Pool


def httpx_client():
    # 进程隔离， 每个进程运行一次
    # 声明一个支持异步的上下文管理器
    return httpx.AsyncClient(
        verify=False,
        timeout=httpx.Timeout(100),
    )


async def example_httpx_work(client: httpx.AsyncClient, task_num):
    # 声明一个支持异步的上下文管理器
    response = await client.get('https://www.baidu.com')
    return task_num, response.text


def example_httpx_send(_pool: Pool, tasks):
    for task_num in tasks:
        _pool.submit(example_httpx_work, task_num)
    _pool.input_over()


def example_httpx_save(_pool):
    for i, w in _pool.iter():
        print(i, len(w))


if __name__ == '__main__':
    stime = time.perf_counter()
    logging.basicConfig(level=logging.INFO)

    pool = Pool(async_client=httpx_client, asyncio_debug=True)
    sd = threading.Thread(target=example_httpx_send, args=(pool, list(range(1000)),))
    sv = threading.Thread(target=example_httpx_save, args=(pool,))

    sv.start()
    sd.start()
    pool.start()

    sd.join()
    sv.join()

    print("time:", time.perf_counter() - stime)