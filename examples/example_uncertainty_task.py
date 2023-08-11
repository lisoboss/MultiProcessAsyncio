#! python
# -*- coding: utf-8 -*-

"""
@Py-V  : 3
@File  : example_uncertainty_task.py
@Author: _
@Date  : 2020/4/21 18:49
@Ide   : PyCharm
@Desc  : 请求库测试...
"""
import logging
import time
from multi_process_asyncio.pool import Pool


async def example_work(client, task_num, count=1):
    # 声明一个支持异步的上下文管理器
    response = await client.get('https://www.baidu.com')
    return task_num, len(response.text), count


async def example_task():
    for task_num in range(1000):
        func = example_work
        args = (task_num, )
        kwargs = {}
        yield func, args, kwargs


async def pipline(task_num, _l, count):
    print(task_num, _l, count)
    pass


async def pipline_error(err, task_num, count):
    if count == 3:
        return
    func = example_work
    args = (task_num, )
    kwargs = dict(count=count+1)
    yield func, args, kwargs


if __name__ == '__main__':
    stime = time.perf_counter()
    logging.basicConfig(level=logging.INFO)
    pool = Pool(async_tasks=example_task,
                async_pipline_successful=pipline,
                async_pipline_error=pipline_error,
                # max_work=1, max_sub_work=5,
                asyncio_debug=False)
    pool.run()
    print("time:", time.perf_counter() - stime)
