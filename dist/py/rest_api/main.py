# fastapi基本引入
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
# 引入类型库
from typing import Optional
# 本地接口定义
from .apis import admin
import ujson
# 替换掉默认的print
from .utils.logging import print
from .utils.redis import get_redis_pool, redis_pubsub, CONST_APP_OUT_CHANNEL
from .utils.websocket import connection_manager


# 全局定义的Fastapi实例
'''附加到app.state
ws连接管理器    ws_manager
'''
app = FastAPI()
# redis发布订阅管理器
rds_pubsub = None
#####app生命周期#####
@app.on_event("startup")
async def startup_event():
    print("app_startup")
    # 启用主消息队列处理,回调函数定义为subscribe_callback
    rds_pubsub = redis_pubsub(await get_redis_pool())
    tsk = await rds_pubsub.open_subscribe_message(subscribe_callback)
    # 启动websocket 连接管理器
    app.state.ws_manager = connection_manager()
    app.state.ws_manager.open()
@app.on_event("shutdown")
async def shutdown_event():
    print('app_shutdown')
    # 关闭连接管理器
    app.state.ws_manager.close()
    # 关闭主消息队列处理
    await rds_pubsub.close_subscribe_message()

async def subscribe_callback(channel_name, data):
    '''
    redis订阅的回调函数
    '''
    msg = data.decode('utf-8')
    if channel_name == CONST_APP_OUT_CHANNEL:  # 该频道用于输出electron的核心进程的控制台信息，直接转发给websocket
        await app.state.ws_manager.broadcast(ujson.dumps({
            'method': 'app_output',
            'params': {
                'message': msg
            }
        }))
#####TODO:定义一个验证Header中的令牌的方法####
async def verify_token_header(request: Request, x_token: Optional[str] = Header(None)):
    if not request.url.path.startswith('/index/'):
        if x_token != "token":
            raise HTTPException(status_code=400, detail="X-Token header invalid")

#####TODO:路由和接口配置#####
# admin接口类配置
app.include_router(
    admin.router,
    prefix="/admin",  # path前缀
    tags=["admin"],  # 标签
    dependencies=[Depends(verify_token_header)],  # Token验证
)

##### 欢迎页#####
@app.get("/")
async def get():
    html_welcome = '''
    欢迎使用OneKey client admin
    '''
    return HTMLResponse(html_welcome)

# 启动命令
# .\bin\python.exe -m uvicorn  --port=9002 --ws=websockets rest_api.main:app
