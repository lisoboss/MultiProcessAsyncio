#! python
# -*- coding: utf-8 -*-

"""
@Py-V  : 3
@File  : tset.py
@Author: lisoboss
@Date  : 2020/4/21 18:49
@Ide   : PyCharm
@Desc  : 描述...
"""

from aiohttp import ClientResponse
from . import crawler


async def bbb(rp: ClientResponse = None):
    if not rp:
        return None
    # print(1111)
    return await rp.text()

if __name__ == '__main__':

    cwr = crawler.Crawler()
    cwr.run()

    for i in range(50):
        item = cwr.get_http_conf(seq=i, url='https://www.baidu.com', rp_callback=bbb)
        cwr.put(item)

    cwr.queue_over()

    values = cwr.get_all()

    print('[-]', len(values))

    with open('./out.txt', 'w', encoding='utf-8') as f:
        for i, v in enumerate(values):
            print(i, str(v), file=f)
