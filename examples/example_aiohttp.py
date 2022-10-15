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
import aiohttp
from multi_process_asyncio.pool import Pool


async def async_worker_handle(_: Pool, async_worker):
    # 进程隔离， 每个进程运行一次
    # 声明一个支持异步的上下文管理器
    timeout = 100
    async with aiohttp.ClientSession(
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
    ) as session:
        await async_worker(dict(session=session))


async def work(item, session=None):
    if session is None:
        print("session is None")
        exit(-500)
    # 声明一个支持异步的上下文管理器
    response = await session.get('https://www.baidu.com')
    text = await response.text()
    return item, text


def send_task(_pool, tasks):
    for task in tasks:
        _pool.submit(work, task)
    _pool.input_over()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    pool = Pool(async_worker_handle=async_worker_handle, asyncio_debug=True)
    pool.start()

    st = threading.Thread(target=send_task, args=(pool, list(range(475611)),))
    st.start()

    for i, w in pool.iter():
        print(i, len(w))

    st.join()
