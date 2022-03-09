/*
export function someMutation (state) {
}
*/
export const SET_connected = (state, v) => {
  state.connected = v
}
export const SET_api_ready = (state, v) => {
  state.api_ready = v
}
export const ADD_serv_events = (state, v) => {
  const max_count = 1024 * 10// 保留的最大日志数据条数
  if (v.k in state.serv_events) {
    if (state.serv_events[v.k].length >= max_count) {
      state.serv_events[v.k].splice(0, 1)
    }
    state.serv_events[v.k].push(v)
  } else state.serv_events[v.k] = [v.v]
}
export const UPDATE_services_status = (state, v) => {
  // 避免替换数组，采用值更新，避免子组件无法响应更改事件
  v.forEach((item) => {
    // 先添加不存在的
    const val = state.services_status.find(i => i.full_name === item.full_name)
    if (!val) {
      state.services_status.push(item)
    }
  })
  state.services_status.forEach((item) => {
    const val = v.find(i => i.full_name === item.full_name)
    if (val) {
      item.status = val.status
      item.last_at = val.last_at
    }
  })
}
