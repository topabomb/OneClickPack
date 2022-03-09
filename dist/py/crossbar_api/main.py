import os
import sys
import asyncio
import ujson
from os import environ
from autobahn.asyncio.wamp import ApplicationRunner
from autobahn.asyncio.component import run
def get_session_class():
    class Session1(MyApplicationSession):
        async def onJoin(self, details):
            # await self.subscribe(self.onEvent, 'core.sevice.out')
            await super().onJoin(details)


            '''
            counter = 0
            while True:
                self.publish('core.sevice.out', counter)
                counter += 1
                await asyncio.sleep(1)
            '''
        async def onEvent(self, evt):
            # 订阅事件演示，最终需要执行异步方法，避免阻塞
            print("Got event: {}".format(evt), end='')
            pass

    return Session1
if __name__ == '__main__':
    print(sys.argv)
    sys.path.append(os.path.dirname(sys.argv[0]))
    from utils.logging import print
    from utils.crossbar import rpc_instances, RpcBase, MyApplicationSession

    url = environ.get("AUTOBAHN_ROUTER", "ws://127.0.0.1:8081/ws")
    realm = environ.get("AUTOBAHN_REALM", "realm1")
    # 获取服务目录
    dir_serv = sys.argv[1] if len(sys.argv) > 1 else ''
    if not os.path.exists(dir_serv):
        dir_serv = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), dir_serv))
    if not os.path.exists(dir_serv):
        dir_serv = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '../../s'))
    runner = ApplicationRunner(url, realm)
    # 支持多模块的RPC注册，默认为当前目录下的rpc_sets
    session = get_session_class()(['rpc_sets'], serv_dir=dir_serv)  # serv_dir为**kwargs扩展参数会传递到rpc_sets类的实例化函数的**kwargs中
    # 启动事件循环
    runner.run(session)
