<template>
  <q-bar>
    <div>
      <span>
        <q-icon v-if="connected" name="flash_on" color="green">
          <q-tooltip>crossbar服务连接完成</q-tooltip>
        </q-icon>
        <q-icon v-else name="flash_off" color="red">
          <q-tooltip>crossbar服务连接失败</q-tooltip>
        </q-icon>
      </span>
    </div>

    <div>
      <span class="mini_font">service:{{ running_services.length }}/{{ status.length }}</span>
      <q-btn
        dense
        flat
        round
        icon="lens"
        size="6.5px"
        color="green"
        class="q-mx-none"
        @click="showServicesStatus"
      ><q-tooltip>服务管理器</q-tooltip></q-btn>
      <q-btn
        flat
        round
        dense
        color="red"
        icon="cancel"
        size="6.5px"
        class="q-mx-none"
        @click="closeRunning"
      ><q-tooltip>全部关闭</q-tooltip></q-btn>
    </div>
    <q-space />
    <div>
      <q-btn flat round dense icon="info" class="mini_font" @click="showOutConsole">
        <q-badge floating>{{ outEvents.length }}</q-badge>
        <q-tooltip>Core日志</q-tooltip>
      </q-btn>
      <q-btn flat round dense icon="warning" class="mini_font" @click="showPrintConsole">
        <q-badge floating color="red">{{ printEvents.length }}</q-badge>
        <q-tooltip>Service日志</q-tooltip>
      </q-btn>
    </div>
  </q-bar>
</template>
<script>
import ServicesStatus from 'components/ServicesStatus.vue'
import EventConsole from 'components/EventConsole.vue'
export default {
  name: 'StatusBar',
  components: { ServicesStatus, EventConsole },
  props: {
    status: {
      type: Array,
      required: true
    },
    outEvents: {
      type: Array,
      required: true
    },
    printEvents: {
      type: Array,
      required: true
    },
    connected: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {}
  },
  computed: {
    running_services: function() {
      return this.status.filter((x) => x.status === 'running')
    }
  },
  methods: {
    showServicesStatus() {
      this.$q.dialog({
        component: ServicesStatus,
        parent: this, // becomes child of this Vue node
        status: this.status
      })
    },
    showOutConsole() {
      this.$q.dialog({
        component: EventConsole,
        parent: this, // becomes child of this Vue node
        events: this.outEvents,
        maximized: true,
        title: 'Core事件查看器',
        fromJson: (v) => v.v
      })
    },
    showPrintConsole() {
      this.$q.dialog({
        component: EventConsole,
        parent: this, // becomes child of this Vue node
        events: this.printEvents,
        maximized: true,
        title: 'Service事件查看器',
        fromJson: (v) => v.msg,
        group: {
          selected:
            this.status && this.status[0] ? this.status[0].full_name : null,
          nameField: 'name',
          groups: this.status.map((v) => {
            return v.full_name
          })
        }
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
    }
  }
}
</script>
<style scoped>
.mini_font {
  font-size: 11px;
  -webkit-transform: scale(0.83);
}
</style>
