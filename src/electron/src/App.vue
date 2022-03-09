<template>
  <div id="q-app">
    <router-view />
  </div>
</template>
<script>
export default {
  name: 'App',
  data() {
    return {
      ready_interval: null,
      autorun_started: false
    }
  },
  created: function() {

  },
  mounted: async function() {
    // this.initWebsocket()
    this.initClient()
  },
  destroyed: async function() {
    await this.$store.dispatch('crossbar/close')
  },
  methods: {
    async initWebsocket(type) {
      const that = this
      if ('WebSocket' in window) {
        console.log('您的浏览器支持 WebSocket!')
        try {
          await that.$store.dispatch('websocket/wsMessageInit', 'ws://localhost:9002/admin/ws/service/user1')
          await that.$store.dispatch('websocket/wsMessageSend', 'welcome')
          await that.$store.dispatch('websocket/wsMessageSend', { msg: 'abc' })
          // await that.$store.dispatch('websocket/wsMessageClose')
        } catch (e) {
          console.log('websocket连接状态', e)
        }
      } else {
        console.log('您的浏览器不支持 WebSocket!')
      }
    },
    async initClient() {
      const that = this
      const session = await that.$store.dispatch('crossbar/open', { url: 'ws://127.0.0.1:8081/ws', realm: 'realm1' })
      const proc = () => {
        return new Promise((resolve, reject) => {
          session.call('sys.ServiceControl.getServiceStatus').then(
            async function(resp) {
              // console.log('sys.ServiceControl.getServiceStatus result:', that.autorun_started,resp,resp.filter(v=>v.autorun&&!v.status||v.status==='stop'))
              // 更新vuex中的service数组
              await that.$store.dispatch('crossbar/updateService', resp)

              if (that.$router.currentRoute.path !== '/exit' && !that.autorun_started && resp.filter(v => v.autorun && v.status && (v.status === 'starting' || v.status === 'running')).length <= 0) { // 第一次启动时时自动运行所有自启动的服务
                setTimeout(() => {
                  that.autorun_started = true
                  that.$q.loadingBar.start()
                  session.call('sys.ServiceControl.autorun_start').then((res) => {
                    console.log('sys.ServiceControl.autorun_start result:', res)
                    that.$q.loadingBar.stop()
                    that.$q.notify({ message: '已启动服务:' + res.toString(), closeBtn: true })
                  }, (err) => {
                    that.$q.loadingBar.stop()
                    console.log('sys.ServiceControl.autorun_start error:', err)
                  })
                }, 100)
              }
              if (!that.ready_interval)that.ready_interval = setInterval(proc, 1000 * 5)// 定期获取服务状态
              that.$store.commit('crossbar/SET_api_ready', true)

              resolve(true)
            },
            function(err) {
              console.log('sys.ServiceControl.getServiceStatus error:', err)
              if (that.ready_interval) {
                clearInterval(that.ready_interval)
                that.ready_interval = null
                that.$store.commit('crossbar/SET_api_ready', false)
              }
              setTimeout(proc, 500 * 1)// 重试
            }
          )
        })
      }
      await proc()
    }
  }
}
</script>
