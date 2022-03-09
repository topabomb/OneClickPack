<template>
  <q-page class="q-pa-xs q-pm-xs bg-grey-9" padding>
    <div v-if="!api_ready||!connected" class="fit row justify-center text-white">
      <q-item class="q-ma-xl">
        <q-spinner-puff color="white" size="xl" />
      </q-item>
    </div>
    <div v-else>
      <q-card v-if="autorun_services.length>0" class="q-ma-sm" flat bordered dense>
        <q-item dense class="q-px-xs q-py-none" style="min-height:24px;">
          <q-item-section>
            <q-item-label class="text-weight-light">关键服务</q-item-label>
          </q-item-section>
          <q-item-section side>
            <q-item-label caption>
              <q-badge color="green" :label="running_services.length" />
              /{{ autorun_services.length }}</q-item-label>
          </q-item-section>
        </q-item>
        <q-separator />
        <q-card-section class="q-ma-none q-pa-none row items-start  q-gutter-xs bg-grey-2">
          <q-card v-for="(service,index) in autorun_services" :key="index" flat dense bordered class="col" style="min-width:160px;">
            <q-item dense class="q-pa-xs" style="min-height:24px;">
              <q-item-section>
                <q-item-label
                  style="display: -webkit-box;-webkit-box-orient: vertical;-webkit-line-clamp: 2;overflow: hidden;"
                >{{ service.full_name }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-item-label>
                  <q-spinner-dots v-if="service.status==='starting'" color="green" size="1.5em" />
                  <q-icon v-else name="lens" :color="service.status==='running'?'green':service.status==='starting'?'yellow':'red'" />
                  <q-btn icon="keyboard_arrow_down" flat round size="sm">
                    <q-menu>
                      <q-list dense style="min-width: 120px">
                        <q-item v-close-popup clickable :disable="service.status==='running'||service.status==='starting'" @click="startService(service)">
                          <q-item-section>启动</q-item-section>
                        </q-item>
                        <q-item v-close-popup clickable :disable="service.status==='stop'||!service.status" @click="stopService(service)">
                          <q-item-section>停止</q-item-section>
                        </q-item>
                        <q-item v-close-popup clickable :disable="service.status==='stop'||service.status==='starting'||(restarting&&restarting.length>0)" @click="restartService(service)">
                          <q-item-section>重新启动</q-item-section>
                        </q-item>
                        <q-separator />
                        <q-item v-close-popup clickable @click="openServiceHome(service)">
                          <q-item-section>CWD目录...</q-item-section>
                        </q-item>
                      </q-list>
                    </q-menu>
                  </q-btn>
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-card>
        </q-card-section>
      </q-card>
      <q-card v-if="available_urls.length>0" class="q-ma-sm" flat bordered dense>
        <q-item dense class="q-px-xs q-py-none" style="min-height:24px;">
          <q-item-section>
            <q-item-label class="text-weight-light">可用网址</q-item-label>
          </q-item-section>
          <q-item-section side>
            <q-item-label caption><q-badge color="green" :label="available_urls.length" /></q-item-label>
          </q-item-section>
        </q-item>
        <q-separator />
        <q-card-section class="q-ma-none q-pa-none row items-start  q-gutter-xs bg-grey-2">
          <q-card v-for="(item,index) in available_urls" :key="index" flat dense bordered class="col " style="min-width:380px;">
            <q-item dense class="q-pa-xs" style="min-height:24px;">

              <q-item-section>
                <q-item-label>{{ item.title }}<q-badge v-if="item.owner" :color="item.top?'primary':'secondary'" style="max-width:120px; overflow:hidden; white-space:nowrap; text-overflow:ellipsis;">
                  {{ item.owner }}
                  <q-tooltip anchor="top middle" self="top middle">
                    {{ item.owner }}
                  </q-tooltip>
                </q-badge>
                </q-item-label>
                <a :href="item.url" target="_blank" style="text-decoration:none">
                  <q-item-label
                    caption
                  >
                    {{ item.url }}

                  </q-item-label>
                </a>
              </q-item-section>

              <q-item-section side>
                <q-item-label>
                  <q-btn icon="content_copy" flat round size="sm" @click="doCopy(item.url)" />
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-card>
        </q-card-section>
      </q-card>

      <GroupsStatus :groups="groups" class="q-ma-sm" />
    </div>
  </q-page>
</template>

<script>
import { mapState } from 'vuex'
import GroupsStatus from 'components/GroupsStatus.vue'
export default {
  name: 'PageIndex',
  components: {
    GroupsStatus
  },
  data() {
    return {
      restarting: null,
      groups: []
    }
  },
  watch: {
    services_status: { // 深度监听，可监听到对象、数组的变化
      handler(val, oldVal) {
        if (this.restarting && this.restarting.length > 0) {
          const restartServ = val.filter((x) => x.full_name === this.restarting)[0]
          if (restartServ && restartServ.status === 'stop') {
            const proc = () => {
              this.$q.loading.show({ message: '正在启动:' + restartServ.full_name })
              this.startService(restartServ)
            }
            setTimeout(proc, 100)
          }
          if (restartServ && restartServ.status === 'running') {
            this.restarting = null
            this.$q.loading.hide()
          }
        }
      },
      deep: true // true 深度监听
    }
  },
  mounted: async function() {
    console.log(this.$q.version)
    await this.getGroupsConfig()
  },
  computed: {
    ...mapState('crossbar', [
      'services_status', 'api_ready', 'connected'
    ]),
    autorun_services: function() {
      return this.services_status.filter((x) => x.autorun === true || x.status === 'running' || x.status === 'starting')
    },
    running_services: function() {
      return this.services_status.filter((x) => x.status === 'running' || x.status === 'starting')
    },
    available_urls: function() {
      const that = this

      const urls = []
      this.groups.forEach((g) => {
        g.urls && g.urls.forEach((u) => {
          u.owner = g.name
          u.top = true
          urls.push(u)
        })
        g.components.forEach((s) => {
          s.urls && that.running_services.findIndex((r) => r.full_name === s.full_name && r.status === 'running') >= 0 && s.urls.forEach((u) => {
            u.owner = s.full_name
            urls.push(u)
          })
        })
      })
      return urls
    }

  },
  methods: {
    async getGroupsConfig() {
      const that = this
      const proc = async() => {
        try {
          const crossbar = await that.$store.dispatch('crossbar/get_session')
          if (!crossbar) throw new Error('crossbar/get_session 未获取到有效的连接')
          const resp = await crossbar.call('sys.ServiceControl.getGroupsConfig')
          that.groups = resp
          console.log('getGroupsConfig success:', resp)
        } catch (err) {
          console.error('getGroupsConfig error:', err)
          setTimeout(proc, 500)
        }
      }
      await proc()
    },
    doCopy: function(text) {
      const that = this
      this.$copyText(text).then((e) => {
        that.$q.dialog({ title: '复制成功', message: `已将${text}复制到剪贴板`
        })
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
    },
    async restartService(service) {
      const that = this
      if (!this.restarting) {
        that.$q.loading.show({ message: '正在停止:' + service.full_name })
        this.restarting = service.full_name
        await this.stopService(service)// 此处stop，由watch处执行start的逻辑
      }
    },
    async openServiceHome(item) {
      const that = this
      const crossbar = await that.$store.dispatch('crossbar/get_session')
      crossbar.call('sys.electron.openpath', [item.cwd]).then(
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
