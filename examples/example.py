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

from multi_process_asyncio.pool import Pool


async def example_work(client, task_num):
    # 声明一个支持异步的上下文管理器
    response = await client.get('https://www.baidu.com')
    return task_num, response.text


def example_send(_pool: Pool, tasks):
    for task_num in tasks:
        _pool.submit(example_work, task_num)
    _pool.input_over()


def example_save(_pool):
    for i, w in _pool.iter():
        print(i, len(w))


if __name__ == '__main__':
    stime = time.perf_counter()
    logging.basicConfig(level=logging.INFO)

    pool = Pool(asyncio_debug=True)
    sd = threading.Thread(target=example_send, args=(pool, list(range(1000)),))
    sv = threading.Thread(target=example_save, args=(pool,))

    sv.start()
    sd.start()
    pool.start()

    sd.join()
    sv.join()

    print("time:", time.perf_counter() - stime)