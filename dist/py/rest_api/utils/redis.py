import aioredis
import asyncio
from .logging import print

CONST_APP_OUT_CHANNEL = 'app_output'
async def get_redis_pool():
    '''
    获取redis连接池
    '''
    try:
        pool = await aioredis.create_redis_pool('redis://localhost:16379',
                                                minsize=2, maxsize=10, encoding='utf-8')
        return pool
    except ConnectionRefusedError as e:
        print('cannot connect to redis on:', REDIS_HOST, REDIS_PORT)
        return None
class redis_pubsub:
    def __init__(self, pool):
        self.pool = pool
        self.subscribe_task = None
    async def subscribe_reader(self, ch, cb=None):
        '''
        阻塞读取指定频道的消息
        使用 asyncio.ensure_future(subscribe_reader(channel)) 启动异步任务
        '''
        while (await ch.wait_message()):
            msg = await ch.get()
            if cb != None:
                await cb(ch.name.decode(), msg)  # 回调函数传递两个参数
    async def open_subscribe_message(self, cb=None):
        pool = self.pool
        channels = await pool.subscribe(CONST_APP_OUT_CHANNEL)
        tsk = asyncio.ensure_future(self.subscribe_reader(channels[0], cb))  # 启动异步任务
        # 不等待结果，直接返回
        # await tsk
        self.subscribe_task = tsk
    async def close_subscribe_message(self):
        pool = self.pool
        if self.subscribe_task != None:
            self.subscribe_task.cancel()
        pool.unsubscribe(CONST_APP_OUT_CHANNEL)
        pool.close()
