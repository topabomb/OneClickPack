<template>
  <div>
    <q-bar class="q-electron-drag">
      <q-icon name="laptop_chromebook" />
      <div class="q-mr-md">
        <span>Oneclick Pack</span>
      </div>
      <q-separator vertical />

      <div>
        <q-btn-group flat>
          <q-btn push label="服务">
            <q-badge dense color="green" size="xs" align="top">{{ running_services.length }}</q-badge>
            <q-menu>
              <q-list dense style="min-width: 100px">
                <q-item v-close-popup clickable @click="startManyService(false)">
                  <q-item-section>启动全部关键服务</q-item-section>
                </q-item>
                <q-item v-close-popup clickable @click="closeRunning">
                  <q-item-section>停止全部服务</q-item-section>
                </q-item>
                <q-item v-close-popup clickable @click="showServicesStatus">
                  <q-item-section>服务管理器...</q-item-section>
                </q-item>
                <q-separator />
                <q-item v-for="(item,index) in status" :key="index" v-close-popup clickable>

                  <q-item-section :class="item.status==='running'||item.status==='starting'?'text-green-10':'text-red-10'">{{ item.full_name }}</q-item-section>
                  <q-item-section side>
                    <div class="q-gutter-xs">
                      <q-spinner-dots
                        v-if="item.status==='starting'"
                        color="green"
                        size="1.2em"
                      />
                      <q-btn v-show="item.status==='stop'||!item.status" size="sm" flat dense round icon="play_arrow" color="green" @click="startService(item)" />
                      <q-btn v-show="item.status==='running'||item.status==='starting'" size="sm" flat dense round icon="stop" color="red" @click="stopService(item)" />
                    </div>
                  </q-item-section>

                </q-item>
              </q-list>
            </q-menu>
          </q-btn>

          <q-btn push label="工具">
            <q-menu auto-close>
              <q-list dense style="min-width: 100px">
                <q-item clickable @click="setDevtools">
                  <q-item-section>DevTools</q-item-section>
                </q-item>
              </q-list>
            </q-menu>
          </q-btn>

        </q-btn-group>

      </div>
      <q-space />
      <q-separator vertical />
      <div>
        <q-btn dense flat icon="minimize" @click="minimize" />
        <q-btn dense flat icon="crop_square" @click="maximize" />
        <q-btn dense flat icon="close" @click="closeApp" />
      </div>
    </q-bar>

  </div>
</template>
<script>
import { mapGetters } from 'vuex'
import ServicesStatus from 'components/ServicesStatus.vue'
export default {
  name: 'MainMenu',
  components: { ServicesStatus },
  props: {
    status: {
      type: Array,
      required: true
    }
  },
  data() {
    return {}
  },
  computed: {
    ...mapGetters('crossbar', [

    ]),
    running_services: function() {
      return this.status.filter((x) => x.status === 'running')
    }
  },
  methods: {
    minimize() {
      if (process.env.MODE === 'electron') {
        this.$q.electron.remote.BrowserWindow.getFocusedWindow().minimize()
      }
    },

    maximize() {
      if (process.env.MODE === 'electron') {
        const win = this.$q.electron.remote.BrowserWindow.getFocusedWindow()

        if (win.isMaximized()) {
          win.unmaximize()
        } else {
          win.maximize()
        }
      }
    },

    closeApp() {
      if (process.env.MODE === 'electron') {
        this.$q.electron.remote.BrowserWindow.getFocusedWindow().close()
      }
    },
    async setDevtools() {
      const that = this
      const crossbar = await that.$store.dispatch('crossbar/get_session')
      crossbar.call('sys.electron.devtools', []).then(
        function(res) {
          console.log('sys.electron.devtools Result:', res)
        },
        function(err) {
          console.error('sys.electron.devtools Error:', err.error, err.args[0])
        },
        function(progress) {
          console.log('sys.electron.devtools Progress:', progress)
        }
      )
    },
    showServicesStatus() {
      this.$q.dialog({
        component: ServicesStatus,
        parent: this, // becomes child of this Vue node
        status: this.status
      })
    },
    async closeRunning() {
      const that = this
      const crossbar = await that.$store.dispatch('crossbar/get_session')
      this.$q
        .dialog({
          cancel: true,
          title: '确认关闭',
          message: '您确认要关闭全部的运行中服务吗'
        })
        .onOk(() => {
          that.$q.loading.show({ message: '正在停止全部运行中的服务!' })
          crossbar.call('sys.ServiceControl.running_stop', []).then(
            function(res) {
              console.log('sys.ServiceControl.running_stop Result:', res)
              that.$q.notify({ message: '停止服务:' + res.toString(), closeBtn: true })
              that.$q.loading.hide()
            },
            function(err) {
              console.error(
                'sys.ServiceControl.running_stop Error:',
                err.error,
                err.args[0]
              )
            }
          )
        })
    },
    async startManyService(startAll) {
      const that = this
      const crossbar = await that.$store.dispatch('crossbar/get_session')
      this.$q
        .dialog({
          cancel: true,
          title: '确认启动',
          message: '您确认要启动全部关键服务吗'
        })
        .onOk(() => {
          that.$q.loading.show({ message: '正在启动关键服务!' })
          crossbar.call('sys.ServiceControl.autorun_start', []).then(
            function(res) {
              console.log('sys.ServiceControl.autorun_start Result:', res)
              that.$q.notify({ message: '启动服务:' + res.toString(), closeBtn: true })
              that.$q.loading.hide()
            },
            function(err) {
              console.error(
                'sys.ServiceControl.autorun_start Error:',
                err.error,
                err.args[0]
              )
            }
          )
        })
    },
    async startService(service) {
      const that = this
      const crossbar = await that.$store.dispatch('crossbar/get_session')
      crossbar.call('sys.ServiceControl.start', [service.full_name]).then(
        function(res) {
          console.log('Result:', res)
        },
        function(err) {
          console.error('Error:', err.error, err.args[0])
        }
      )
    },
    async stopService(service) {
      const that = this
      const crossbar = await that.$store.dispatch('crossbar/get_session')
      crossbar.call('sys.ServiceControl.stop', [service.full_name]).then(
        function(res) {
          console.log('Result:', res)
        },
        function(err) {
          console.error('Error:', err.error, err.args[0])
        }
      )
    }
  }
}
</script>
