/*
export function someMutation (state) {
}
*/
export const wsMessageChange = (state) => {
  state.wsMessage.connected = state.wsMessage.sock && state.wsMessage.sock.readyState === 1
}
export const wsMessageSetSock = (state, val) => {
  state.wsMessage.sock = val
}
export const wsMessageSetIdle = (state, val) => {
  state.wsMessage.idle_interval = val
}
export const wsMessageAddMessage = (state, val) => {
  state.wsMessage.messages.push(val)
}
