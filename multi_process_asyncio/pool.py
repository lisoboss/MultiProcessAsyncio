#! python
# -*- coding: utf-8 -*-

"""
@Py-V  : 3.7
@File  : pool.py
@Author: _
@Date  : 2020/4/16 16:28
@Ide   : PyCharm
@Desc  : 多进程 + 协程 HTTP请求库...
# pip install aiohttp[speedups]
"""

import asyncio
from logging import getLogger
from functools import wraps
from multiprocessing import (
    Pool as _Pool,
    Manager,
    cpu_count
)


LOG = getLogger(__name__)


def logger(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        LOG.debug("%s => args: %s, kwargs: %s", func.__name__, args, kwargs)
        ret = func(*args, **kwargs)
        LOG.debug("%s => ret: %s", func.__name__, ret)
        return ret
    return wrapper


class _Over:
    pass


class QueueManager(object):

    def __init__(self, max_work, max_sub_work):
        self.max_work = max_work
        self.max_sub_work = max_sub_work

        self.input = Manager().Queue()
        self.output = Manager().Queue()

    @logger
    def push_input(self, *args, **kwargs):
        return self.input.put(*args, **kwargs)

    @logger
    def push_output(self, *args, **kwargs):
        return self.output.put(*args, **kwargs)

    @logger
    def pop_input(self, *args, **kwargs):
        return self.input.get(*args, **kwargs)

    @logger
    def pop_output(self, *args, **kwargs):
        return self.output.get(*args, **kwargs)

    async def sync_io(self, _input):
        while True:
            for _ in range(100):
                ret = self.pop_input()
                if ret == _Over:
                    for _ in range(self.max_sub_work):
                        await _input.put(ret)
                    break
                await _input.put(ret)
            await asyncio.sleep(0.3)


class Pool(object):

    def __init__(self, async_callback, max_work=cpu_count(), max_sub_work=100):
        self.max_work = max_work
        self.max_sub_work = max_sub_work
        self._queue_manager = QueueManager(max_work, max_sub_work)
        self._pool = _Pool(max_work)
        self.async_callback = async_callback
        self._input_over = False

    def __getstate__(self):
        self_dict = self.__dict__.copy()
        del self_dict['_pool']
        return self_dict

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __del__(self):
        LOG.info('[-] ==== Pool Close ====')

    async def _async_work(self, queue):
        while True:
            item = await queue.get()
            if item == _Over:
                self._queue_manager.push_output(item)
                break
            self._queue_manager.push_output(await self.async_callback(item))

    async def _async_main(self, _i):
        LOG.debug('[+] _async_main start => %s', _i)
        queue = asyncio.Queue()

        tasks = [asyncio.create_task(self._queue_manager.sync_io(queue))]

        for _ in range(self.max_sub_work):
            tasks.append(asyncio.create_task(self._async_work(queue)))

        await asyncio.gather(*tasks)

        for _task in tasks:
            _task.cancel()
        LOG.debug('[+] _async_main end => %s', _i)

    def _work(self, _i):
        LOG.debug('[+] _work start => %s', _i)
        asyncio.run(self._async_main(_i), debug=False)
        LOG.debug('[+] _work end => %s', _i)

    def submit(self, item):
        if self._input_over:
            return print("input is close")
        return self._queue_manager.push_input(item)

    def input_over(self):
        if self._input_over:
            return print("input is true")
        self._input_over = True
        for _ in range(self.max_work):
            self._queue_manager.push_input(_Over)

    def iter(self):
        i = 0
        n = self.max_work * self.max_sub_work
        while i < n:
            ret = self._queue_manager.pop_output()
            if ret == _Over:
                i += 1
                continue
            yield ret

    def start(self):
        LOG.info('[+] ==== Pool Running ====')
        for _i in range(self.max_work):
            self._pool.apply_async(func=self._work, args=(_i + 1,))
        self._pool.close()
