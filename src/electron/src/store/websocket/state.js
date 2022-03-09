export default function() {
  return {
    // 主消息通道
    wsMessage: {
      sock: null, // ws实例
      connected: false, // 是否连接
      idle_interval: null, // 心跳的interval句柄
      events: [], // 已订阅的事件
      messages: [] // 已收到的消息列表
    }
  }
}
