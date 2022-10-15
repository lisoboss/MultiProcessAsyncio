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
import httpx
from multi_process_asyncio.pool import Pool


async def async_worker_handle(_: Pool, async_worker):
    # 进程隔离， 每个进程运行一次
    # 声明一个支持异步的上下文管理器
    async with httpx.AsyncClient(
            verify=False,
            timeout=httpx.Timeout(100),
    ) as client:
        await async_worker(dict(client=client))


async def work(item, client: httpx.AsyncClient = None):
    if client is None:
        print("client is None")
        exit(-500)
    # 声明一个支持异步的上下文管理器
    response = await client.get('https://www.baidu.com')
    return item, response.text


def send_task(_pool, tasks):
    for task in tasks:
        _pool.submit(work, task)
    _pool.input_over()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    pool = Pool(async_worker_handle=async_worker_handle, asyncio_debug=True)
    pool.start()

    st = threading.Thread(target=send_task, args=(pool, list(range(1000)),))
    st.start()

    for i, w in pool.iter():
        print(i, len(w))

    st.join()
