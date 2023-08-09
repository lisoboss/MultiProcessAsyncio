#! python
# -*- coding: utf-8 -*-

"""
@Py-V  : 3.7
@File  : pool.py
@Author: _
@Date  : 2020/4/16 16:28
@Ide   : PyCharm
@Desc  : 多进程 + 协程 HTTP请求库...
# pip install httpx
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
from .httpx import default_client


LOG = getLogger(__name__)


def logger(h=True, e=True):

    def logger_func(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if h:
                LOG.debug("%s => args: %s, kwargs: %s", func.__name__, args, kwargs)
            ret = func(*args, **kwargs)
            if e:
                LOG.debug("%s => ret: %s", func.__name__, ret)
            return ret
        return wrapper
    return logger_func


class _Over:
    def __init__(self):
        pass


class QueueManager(object):

    def __init__(self, max_work, max_sub_work):
        m = Manager()

        self.max_work = max_work
        self.max_sub_work = max_sub_work

        self.input = m.Queue()
        self.output = m.Queue()

    @logger(e=False)
    def push_input(self, *args, **kwargs):
        return self.input.put(*args, **kwargs)

    @logger()
    def push_output(self, *args, **kwargs):
        return self.output.put(*args, **kwargs)

    @logger()
    def pop_input(self, *args, **kwargs):
        return self.input.get(*args, **kwargs)

    @logger(h=False)
    def pop_output(self, *args, **kwargs):
        return self.output.get(*args, **kwargs)

    async def sync_io(self, _input):
        while True:
            ret = self.pop_input()
            if ret == _Over:
                for _ in range(self.max_sub_work):
                    await _input.put(ret)
                break
            await _input.put(ret)
            await asyncio.sleep(0)


class Pool(object):

    def __init__(self, max_work=None, max_sub_work=None, async_client=None, asyncio_debug=False):
        self.max_work = max_work or cpu_count()
        self.max_sub_work = max_sub_work or 100
        self._pool = _Pool(self.max_work)
        self._queue_manager = QueueManager(self.max_work, self.max_sub_work)
        self.asyncio_debug = asyncio_debug
        self._input_over = False
        self.async_client = async_client or default_client

    def __getstate__(self):
        self_dict = self.__dict__.copy()
        del self_dict['_pool']
        return self_dict

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __del__(self):
        LOG.info('[-] ==== Pool Close ====')

    async def _async_work(self, queue, client):
        while True:
            item = await queue.get()
            if item == _Over:
                self._queue_manager.push_output(item)
                break
            async_callback, args, kwargs = item
            self._queue_manager.push_output(await async_callback(client, *args, **kwargs))

    def _asyncio_set_tasks(self, loop, client, _i):
        queue = asyncio.Queue()
        loop.create_task(self._queue_manager.sync_io(queue), name=f'Process:{_i}, Task:queue')

        for _ii in range(self.max_sub_work):
            loop.create_task(self._async_work(queue, client=client), name=f'Process:{_i}, Task:{_ii + 1}')

    def _work(self, _i):
        client = self.async_client()
        assert client, "session is None"

        loop = asyncio.new_event_loop()
        loop.set_debug(self.asyncio_debug)

        if asyncio.iscoroutine(client):
            client = loop.run_until_complete(client)

        aclient = loop.run_until_complete(client.__aenter__())

        self._asyncio_set_tasks(loop, aclient, _i)
        try:
            loop.run_forever()
        finally:
            loop.run_until_complete(client.__aexit__())
            loop.close()

    def submit(self, async_callback, *args, **kwargs):
        if self._input_over:
            return print("input is close")
        return self._queue_manager.push_input((async_callback, args, kwargs))

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
