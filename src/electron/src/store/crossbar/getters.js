/*
export function someGetter (state) {
}
*/
export function connected(state) {
  return state.connected
}
export function api_ready(state) {
  return state.api_ready
}
export function evtCoreServiceOut(state) {
  return state.serv_events['core.sevice.out']
}
export function evtCoreServicePrint(state) {
  return state.serv_events['core.sevice.print']
}
export function arrCoreServiceStatus(state) {
  return state.services_status
}
