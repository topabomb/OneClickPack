/*
export function someAction (context) {
}
*/
import autobahn from 'autobahn'
// 唯一实例的对象
const crossbar = {
  connection: null,
  subscribe_events: {},
  register_funcs: {},
  get_session: function() {
    if (this.connection) return this.connection.session
    else console.error('get_session错误，未能访问crossbar连接')
  },
  open: function(url, realm, onClose) {
    const that = this
    if (!this.connection) {
      const conn = new autobahn.Connection({
        use_es6_promises: true,
        url: url, realm: realm,
        on_user_error: (error, customErrorMessage) => {
          console.error('on_user_error', error, customErrorMessage)
        },
        on_internal_error: (error, customErrorMessage) => {
          console.error('on_internal_error', error, customErrorMessage)
        }
      })
      conn.onopen = (s) => {
        console.log('Crossbar connection connected.')
        that.connection = conn
        // 重新订阅已经订阅的事件
        for (const k in that.subscribe_events) {
          that.subscribe(k, that.subscribe_events[k].fn)
        }
        // 重新注册已经注册的函数
        for (const k in that.register_funcs) {
          that.register(k, that.register_funcs[k].fn)
        }
      }
      conn.onclose = (reason, details) => {
        console.log('Crossbar connection lost: ' + reason, details)
        that.connection = null
        if (onClose) onClose()
      }
      conn.open()
    }
  },
  close: function() {
    const that = this
    if (that.connection) that.connection.close()
  },
  subscribe: function(name, fn) {
    const that = this
    that.connection.session.subscribe(name, fn).then((s) => {
      console.log(`订阅${name}成功`)
      that.subscribe_events[name] = { s: s, fn: fn }
    }, (err) => {
      console.log(`订阅${name}失败!`, err)
    })
  },
  register: function(name, fn) {
    const that = this
    that.connection.session.register(name, fn).then((r) => {
      console.log(`注册${name}成功`)
      that.register_funcs[name] = { s: r, fn: fn }
    }, (err) => {
      console.log(`注册${name}失败!`, err)
    })
  }
}
export function updateService({ commit, state }, args) {
  commit('UPDATE_services_status', args)
}
export function get_session() {
  return crossbar.get_session()
}
export function open({ commit, state }, args) {
  crossbar.open(args.url, args.realm, () => {
    commit('SET_connected', false)// 连接被断开的回调
  })
  return new Promise((resolve, reject) => {
    const proc = () => {
      if (!crossbar.connection) setTimeout(proc, 100)
      else {
        commit('SET_connected', true)// 连接成功
        // 订阅消息,从state中读取
        for (const k in state.serv_events) {
          if (k === 'core.sevice.status') { // 特别处理服务状态变更
            crossbar.subscribe(k, (e) => {
              commit('UPDATE_services_status', e[0])
            })
          } else {
            crossbar.subscribe(k, (e) => {
              commit('ADD_serv_events', { k: k, v: e[0] })
            })
          }
        }
        // 注册函数
        const funcClientQuit = (args) => {
          console.log(args)
        }
        crossbar.register('web.ui.quit', funcClientQuit)
        // 返回
        resolve(crossbar.connection.session)
      }
    }
    proc()
  })
}
export function close({ commit, state }, args) {
  crossbar.close()
  commit('SET_connected', false)
}
