import aiohttp


async def default_client():
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
