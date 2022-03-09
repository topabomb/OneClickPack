export default function() {
  return {
    _writeBuffer1: [], // 临时写入的buffer
    connected: false,
    api_ready: false,
    services_status: [], // 同步服务状态
    serv_events: {
      'core.sevice.out': [], // core的依赖服务输出
      'core.sevice.print': [], // 已安装服务包的日志输出
      'core.sevice.status': [] // 服务状态更改日志输出，废弃
    }
  }
}
