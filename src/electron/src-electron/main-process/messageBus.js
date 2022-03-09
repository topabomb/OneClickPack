// 引入 events 模块
const events = require('events')
// 公用的消息类,即为消息总线，其他文件可引入发送消息或响应消息
const msgBus = {
  app: new events.EventEmitter(), // 全局
  service: new events.EventEmitter()// 服务类
}
export default msgBus

