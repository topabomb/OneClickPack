
import time
import asyncio
from .logging import print
from fastapi import WebSocket, WebSocketDisconnect
class connection_manager:
    def __init__(self):
        '''
        Key:str,
        Value={
            key:str
            sock:Websocket
            last:Time
        }
        '''
        self.connections = {}
    def open(self):
        pass
    def close(self):
        self.connections = null
        pass
    async def __recv_message(self, key, ws, cb=None):
        try:
            while True:
                data = await ws.receive_text()
                print('key:%s at %s is recv length:%s' % (key, ws.client, len(data)))
                if cb != None:
                    await cb(ws, key, data)
        except WebSocketDisconnect:
            await self.disconnect(key)
        except asyncio.CancelledError:
            await self.disconnect(key)

    async def connect(self, key, ws, cb=None):
        if key in self.connections:  # 连接存在，断开重新设置连接
            await self.disconnect(key)
        await ws.accept()
        print('key:%s at %sis connected!' % (key, ws.client))
        conn = {
            'key': key,
            'sock': ws,
            'last': time.time(),
            'task': asyncio.ensure_future(self.__recv_message(key, ws, cb))
        }
        self.connections[key] = conn

        return self.connections[key]['task']
    async def disconnect(self, key):
        if key in self.connections:
            conn = self.connections.pop(key)
            if conn['sock'].client_state.name == 'CONNECTED':
                await conn['sock'].close()  # 这里会触发__recv_message中断开连接的逻辑
            conn['task'].cancel()
            print('key:%s at %s is disconnected!' % (key, conn['sock'].client))
            conn = None

    async def send(self, key, msg):
        if key in self.connections:
            conn = self.connections[key]
            if conn['sock'].client_state.name == 'CONNECTED':
                await conn['sock'].send_text(msg)

    async def broadcast(self, msg: str):
        for conn in self.connections.values():
            if conn['sock'].client_state.name == 'CONNECTED':
                await conn['sock'].send_text(msg)
