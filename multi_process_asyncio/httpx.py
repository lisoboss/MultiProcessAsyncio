import httpx


def default_client():
    # 进程隔离， 每个进程运行一次
    # 声明一个支持异步的上下文管理器
    return httpx.AsyncClient(
        verify=False,
        timeout=httpx.Timeout(100),
    )


