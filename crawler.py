#! python
# -*- coding: utf-8 -*-

"""
@Py-V  : 3.7
@File  : crawler.py
@Author: lisoboss
@Date  : 2020/4/16 16:28
@Ide   : PyCharm
@Desc  : 多进程 + 协程 HTTP请求库...
# pip install aiohttp[speedups]
"""

import aiohttp
import asyncio
from enum import Enum
from multiprocessing import (
    Pool,
    Manager,
    cpu_count
)


class Method(Enum):
    CONNECT = 'CONNECT'
    HEAD = 'HEAD'
    GET = 'GET'
    DELETE = 'DELETE'
    OPTIONS = 'OPTIONS'
    PATCH = 'PATCH'
    POST = 'POST'
    PUT = 'PUT'
    TRACE = 'TRACE'


class Crawler(object):

    def __init__(self, pool_number=cpu_count()):
        self._pool_number = pool_number
        self._pool = Pool(pool_number)
        self._queue_task = Manager().Queue()
        self._queue_result = Manager().Queue()
        self._queue_run = Manager().Queue()
        self._queue_put_over_key = None
        self._timeout = 30
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br, *',
            'Connection': 'close',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }

        self._status_task = 1
        self._status_result = 2
        self._status_over = 0
        self._status_exit = -1

        self.pool_is_close = False

        self.method = Method

    def __getstate__(self):
        self_dict = self.__dict__.copy()
        del self_dict['_pool']
        return self_dict

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __del__(self):
        print(f'[-] ==== Crawler Close ====')

    def set_http_conf(self, headers=None, timeout=None):
        if headers:
            self._headers = headers
        if timeout:
            self._timeout = timeout

    def get_http_conf(self,
                      seq: int = None,
                      method: Method = Method.GET,
                      url: str = None,
                      data: dict = None,
                      json: dict = None,
                      params: dict = None,
                      flag: str = None,
                      rp_callback=None,
                      allow_redirects: bool = True):
        return {
            'seq': seq,
            'flag': flag,
            'method': method,
            'url': url,
            'data': data,
            'json': json,
            'params': params,
            'headers': self._headers,
            'timeout': self._timeout,
            'rp_callback': rp_callback,
            'allow_redirects': allow_redirects
        }

    def get(self, **kwargs):
        _key, _value = tuple(self._queue_result.get(**kwargs))
        return _value

    def put(self, _item, **kwargs):
        if self.pool_is_close:
            return
        _item = [self._status_task, _item]
        self._queue_task.put(_item, **kwargs)

    def queue_over(self, _item=None, **kwargs):
        _item = [self._status_over, _item]
        for _i in range(self._pool_number):
            self._queue_task.put(_item, **kwargs)

    def queue_start(self):
        for _i in range(self._pool_number):
            self._queue_run.put(self._status_task)

    def queue_exit(self):
        self.pool_is_close = True
        for _i in range(self._pool_number):
            self._queue_run.put(self._status_exit)

    def get_all(self, **kwargs):
        _i = 0
        _n = pow(self._pool_number, 2)
        _values = []
        while True:
            _key, _value = tuple(self._queue_result.get(**kwargs))
            if _key == self._status_over:
                _i += 1
                if _i == _n:
                    break
                continue
            _values.append(_value)
        return _values

    async def _func_asy(self, _async_queue_task, se, _i):
        # print(f'[+] _func_asy_i => {_i}')
        while True:
            _key, _value = tuple(await _async_queue_task.get())
            if _key == self._status_exit or _key == self._status_over:
                self._queue_result.put([self._status_over, None])
                break

            seq = _value['seq']
            method = _value['method']
            if not isinstance(method, str):
                method = method.value
            url = _value['url']
            data = _value['data']
            json = _value['json']
            params = _value['params']
            flag = _value['flag']
            headers = _value['headers']
            timeout = _value['timeout']
            rp_callback = _value['rp_callback']
            allow_redirects = _value['allow_redirects']

            print(f'[+] seq => {seq} | url => {url}')

            result = None
            try:
                timeout = aiohttp.ClientTimeout(total=timeout)
                async with se.request(method=method,
                                      url=url,
                                      headers=headers,
                                      data=data,
                                      json=json,
                                      params=params,
                                      timeout=timeout,
                                      ssl=False,
                                      allow_redirects=allow_redirects) as rp:
                    if rp_callback:
                        result = await rp_callback(rp)
                    else:
                        result = await rp.read()

            except Exception as e:
                print(f'[+] seq => {seq} | url => {url} | ben_an_BaseException: {e}')

            self._queue_result.put([self._status_result, [seq, flag, result]])
            # print(f'[-] seq => {seq} | result_byte_len => {len(result_byte)}')

    async def _func_send_asy(self, _async_queue_task):
        while True:
            _key_value = self._queue_task.get()
            _key, _value = tuple(_key_value)
            if _key == self._status_exit or _key == self._status_over:
                for _i in range(self._pool_number):
                    await _async_queue_task.put(_key_value)
                break

            await _async_queue_task.put(_key_value)

    async def _func_asy_run(self, _i):
        # print(f'[+] _func_asy_run start => {_i}')
        _async_queue_task = asyncio.Queue()
        tasks = [asyncio.create_task(self._func_send_asy(_async_queue_task))]
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as se:
            tasks.extend([asyncio.create_task(self._func_asy(_async_queue_task, se, [_i, _j])) for _j in range(self._pool_number)])

            await asyncio.gather(*tasks)

        for _task in tasks:
            _task.cancel()
        # print(f'[-] _func_asy_run end => {_i}')

    def _func_pool_run(self, _i):
        # print(f'[+] _func_pool_run start => {_i}')
        while True:
            _value = self._queue_run.get()
            if _value == self._status_exit:
                break

            # print(f'[+] _async_run start => {_i}')
            asyncio.run(self._func_asy_run(_i), debug=False)
            # print(f'[-] _async_run end => {_i}')

        # print(f'[-] _func_pool_run end => {_i}')

    def run(self):
        print(f'[+] ==== Crawler Running ====')
        self.queue_start()

        for _i in range(self._pool_number):
            self._pool.apply_async(func=self._func_pool_run, args=(_i,))

        self._pool.close()
        # print(f'[-] ==== run end ====')


# async def bbb(rp: aiohttp.ClientResponse = None):
#     if not rp:
#         return None
#     print(1111)
#     return await rp.text()

# if __name__ == '__main__':
#     zt = time.time()
#
#     cwr = Crawler()
#     cwr.run()
#
#     tt = time.time()
#     print(f'[-] time => {tt}')
#
#     for i in range(50):
#         # item = cwr.get_http_conf(i, 'https://www.baidu.com', rp_callback=bbb)
#         item = cwr.get_http_conf(i, 'https://www.baidu.com')
#         cwr.put(item)
#
#     cwr.queue_over()
#
#     values = cwr.get_all()
#
#     ttt = time.time()
#     print('[-]', ttt, tt, ttt - tt)
#
#     print('[-]', len(values))
#
#     with open('./out.txt', 'w', encoding='utf-8') as f:
#         for i, v in enumerate(values):
#             print(i, str(v), file=f)
#
#     ztt = time.time()
#     print('[-][-]', ztt, zt, ztt - zt)
