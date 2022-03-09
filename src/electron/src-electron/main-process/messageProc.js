import msgBus from './messageBus'

import services from './services'
msgBus.app.on('app_start', function(callback) {
  console.log('app:app_start', callback)
  services.app_start(callback).then((resp) => {
    callback && callback()
  })
})

msgBus.app.on('app_stop', function(callback) {
  console.log('app:app_stop', callback)
  services.app_stop().then((resp) => {
    callback && callback()
  })
})

msgBus.app.on('service_start', function(callback) {
  console.log('app:service_start', callback)
  callback && callback()
})

msgBus.app.on('service_stop', function(callback) {
  console.log('app:service_stop', callback)
  services.service_stopall(callback).then((resp) => {
    callback && callback()
  }, (err) => {
    console.error('app:service_stop error:', err)
    callback && callback()
  })
})
