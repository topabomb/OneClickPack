# fastApi的相关引入，Query定义url中参数的约束和描述，Path定义路径中的约束和描述
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Path, Cookie, Header, Request, Response
# pydantic，BaseModel用于Request与Response的类型定义,Field用于对象属性的约束和描述
from pydantic import BaseModel, Field
# python自带的类型，Optional为可选参数,List等指向python自带的组合类型
from typing import Optional, List, Dict, Set
# fastapi的额外response类型
from fastapi.responses import HTMLResponse, ORJSONResponse, RedirectResponse, StreamingResponse

from ..utils.logging import print
import asyncio

router = APIRouter()


@router.get("/", summary="index", response_class=HTMLResponse)
async def index():
    html_content = """
    <html>
    <body>
    <h1>Admin仅允许websocket的访问方式</h1>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

# websocket处理
@router.websocket("/ws/service/{client}")
async def websocket_service(ws: WebSocket, client: str):
    manager = ws.app.state.ws_manager
    tsk = await manager.connect(client, ws, websocket_recv_callback)
    try:
        await manager.send(client, 'helloworld')
        await tsk
    except asyncio.CancelledError:
        print('key:%s task已被取消' % client)
# websocket接收到消息的回调函数，必须是异步方法并接受至少三个参数
async def websocket_recv_callback(ws: WebSocket, client, msg):
    manager = ws.app.state.ws_manager
    await manager.send(client, msg)
