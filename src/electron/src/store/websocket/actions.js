/*
export function someAction (context) {
}
*/

function make_subscribe_message(event) {
  const msg = {
    method: 'subscribe',
    params: {
      event: event
    }
  }
  return msg
}
function make_unsubscribe_message(event) {
  const msg = {
    method: 'unsubscribe',
    params: {
      event: event
    }
  }
  return msg
}

export function wsMessageInit({ commit, state }, url) {
  if (!state.wsMessage.sock || state.wsMessage.sock.readyState !== 1) {
    const websock = new WebSocket(url)
    commit('wsMessageSetSock', websock)
    websock.onopen = function() {
      console.log('连接成功！')
      commit('wsMessageChange')
      state.wsMessage.events.forEach(e => {
        console.log('重新订阅:' + e)
        websock.send(JSON.stringify(make_subscribe_message(e)))
      })
    }
    websock.onmessage = function(cb) {
      console.log('ws接收！')
      commit('wsMessageChange')
      try {
        const data = JSON.parse(cb.data)
        if (data.method && data.method === 'app_output') console.warn('app_output:', data.params.message)
        commit('wsMessageAddMessage', data)
      } catch (e) {
        console.error('ws消息无法转为json格式', cb.data)
        commit('wsMessageAddMessage', cb.data)
      }
    }
    websock.οnerrοr = function(e) { // 错误
      console.error('ws错误!', e)
      commit('wsMessageChange')
    }
    websock.onclose = function(e) { // 关闭
      const notry = !state.wsMessage.idle_interval// 判断是否重试，手工关闭连接会清空该句柄
      console.log('ws关闭！notry:', notry)
      clearInterval(state.wsMessage.idle_interval)
      commit('wsMessageSetIdle', null)
      commit('wsMessageChange')
      commit('wsMessageSetSock', null)
      if (!notry) {
        setTimeout(() => {
          if (websock == null || websock.readyState !== 1) {
            console.log('尝试重连！')
            wsMessageInit({ commit, state }, url)
          }
        }, 60 * 1000)
      }
    }
    websock.binaryType = 'arraybuffer'
    // 心跳处理
    const idle = setInterval(function() {
      if (websock.readyState !== 1) {
        console.log('ws不是就绪状态！' + websock.readyState)
        clearInterval(state.wsMessage.idle_interval)
        return
      }
      console.log('ws发送心跳！2分钟间隔')
      var heart = {
        method: 'heart',
        params: {}
      }
      websock.send(JSON.stringify(heart))
    }, 2 * 60 * 1000)
    commit('wsMessageSetIdle', idle)
    // 等待连接状态更新
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (websock && websock.readyState === 1) {
          resolve(true)
        } else {
          reject(false)
        }
      }, 500)
    })
  }
}
export function wsMessageSend({ commit, state }, msg) {
  const websock = state.wsMessage.sock
  commit('wsMessageChange')
  if (websock && websock.readyState === 1) {
    const data = typeof (msg) === 'string' ? msg : JSON.stringify(msg)
    console.log('ws发送！', typeof (msg), data)
    websock.send(data)
  }
}
export function wsMessageClose({ commit, state }) {
  const websock = state.wsMessage.sock
  if (websock && websock.readyState === 1) {
    console.log('ws手工关闭!')
    websock.close()
    clearInterval(state.wsMessage.idle_interval)
    commit('wsMessageSetIdle', null)
    commit('wsMessageChange')
    commit('wsMessageSetSock', null)
  }
}
