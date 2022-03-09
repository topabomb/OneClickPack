<template>
  <div>
    <q-card class="q-ma-none" flat bordered dense>
      <q-expansion-item
        expand-separator
        icon="medical_services"
        label="本地服务状态"
        :caption="`共${global_state.package_count}个服务包，${global_state.service_count}个服务，${global_state.url_count}个网址`"
        dense
        value
      >
        <q-separator />
        <q-card-section class="q-ma-none q-pa-none row items-start q-gutter-xs bg-grey-2">
          <q-card
            v-for="(item, index) in groups_status"
            :key="index"
            flat
            dense
            bordered
            class="col"
            style="min-width: 250px"
          >
            <q-item dense class="q-pa-xs" style="min-height: 24px">
              <q-item-section>
                <q-item-label
                  style="
                    display: -webkit-box;
                    -webkit-box-orient: vertical;
                    -webkit-line-clamp: 1;
                    overflow: hidden;
                  "
                >#{{ index }}:{{ item.name }}</q-item-label>
                <q-item-label
                  caption
                  style="
                    display: -webkit-box;
                    -webkit-box-orient: vertical;
                    -webkit-line-clamp: 3;
                    overflow: hidden;
                  "
                >{{ item.description }}</q-item-label>
                <q-separator />
                <q-item-label caption>
                  <q-badge color="green" :label="item.running_services.length" />/
                  <q-badge color="blue" :label="item.autorun_services.length" />
                  / {{ item.components.length }}个服务，
                  <q-badge>{{ item.all_urls_count }}</q-badge>个网址
                </q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-item-label>
                  <q-btn icon="keyboard_arrow_down" flat round size="md">
                    <q-menu dense>
                      <q-list dense style="min-width: 120px">
                        <q-item v-close-popup clickable @click="startGroup(item, true)">
                          <q-item-section>
                            启动自启动服务({{
                              item.autoruns.length
                            }}个)
                          </q-item-section>
                        </q-item>
                        <q-item v-close-popup clickable @click="startGroup(item, false)">
                          <q-item-section>全部启动</q-item-section>
                        </q-item>
                        <q-item v-close-popup clickable @click="stopGroup(item)">
                          <q-item-section>全部停止</q-item-section>
                        </q-item>
                        <q-separator />
                        <q-item v-close-popup clickable @click="openGropHome(item)">
                          <q-item-section>组主目录...</q-item-section>
                        </q-item>
                        <q-separator />
                        <q-list dense separator>
                          <q-item
                            v-for="(s_item, s_index) in services_status.filter((x) => x.group === item.name)"
                            :key="s_index"
                            v-close-popup
                            :class="s_item.status==='running'||s_item.status==='starting'?'text-green-10':'text-red-10'"
                          >
                            <q-item-section>
                              {{
                                s_item.name
                              }}
                            </q-item-section>
                            <q-item-section side>
                              <div class="q-gutter-xs">
                                <q-spinner-dots v-if="s_item.status==='starting'" color="green" size="1.5em" />
                                <q-btn v-show="s_item.status==='stop'||!s_item.status" size="sm" flat dense round icon="play_arrow" color="green" @click="startService(s_item)" />
                                <q-btn v-show="s_item.status==='running'||s_item.status==='starting'" size="sm" flat dense round icon="stop" color="red" @click="stopService(s_item)" />
                              </div>
                            </q-item-section>
                          </q-item>
                        </q-list>
                      </q-list>
                    </q-menu>
                  </q-btn>
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-card>
        </q-card-section>
      </q-expansion-item>
    </q-card>
  </div>
</template>
<script>
import { mapState } from 'vuex'
export default {
  props: {
    groups: {
      type: Array,
      required: true
    },
    copy: {
      type: Function,
      required: false,
      default: () => {
        console.error('未提供复制方法')
      }
    }
  },
  data() {
    return {}
  },
  computed: {
    ...mapState('crossbar', ['services_status']),
    autorun_services: function() {
      return this.services_status.filter((x) => x.autorun === true)
    },
    running_services: function() {
      return this.services_status.filter(
        (x) => x.status === 'running' || x.status === 'starting'
      )
    },
    groups_status: function() {
      const that = this
      return this.groups.map((g) => {
        // 自启动的服务
        g.autorun_services = g.components.filter((s) => {
          return !!that.autorun_services.find(
            (r) => r.full_name === s.full_name
          )
        })
        // 运行中的服务
        g.running_services = g.components.filter((s) => {
          return !!that.running_services.find(
            (r) => r.full_name === s.full_name
          )
        })
        // 全部注册的网址
        let all_urls_count = g.urls ? g.urls.length : 0
        g.components.forEach((s) => {
          all_urls_count += s.urls ? s.urls.length : 0
        })
        g.all_urls_count = all_urls_count
        // 增加了新的属性
        return g
      })
    },
    global_state: function() {
      const package_count = this.groups_status.length
      let service_count = 0
      let url_count = 0
      this.groups_status.forEach((g) => {
        service_count += g.components ? g.components.length : 0
        url_count += g.urls ? g.urls.length : 0
        g.components.forEach((s) => {
          url_count += s.urls ? s.urls.length : 0
        })
      })
      return { package_count, service_count, url_count }
    }
  },
  mounted: async function() { },
  methods: {
    async startGroup(group, only_autorun) {
      const that = this
      const crossbar = await that.$store.dispatch('crossbar/get_session')
      that.$q.loading.show({ message: '正在启动组:' + group.name })
      crossbar
        .call('sys.ServiceControl.group_start', [group.name, only_autorun])
        .then(
          function(res) {
            console.log('Result:', res)
            that.$q.notify({
              message: '成功启动:' + res.toString(),
              closeBtn: true
            })
            that.$q.loading.hide()
          },
          function(err) {
            console.error('Error:', err.error, err.args[0])
            that.$q.loading.hide()
          }
        )
    },
    async stopGroup(group) {
      const that = this
      const crossbar = await that.$store.dispatch('crossbar/get_session')
      that.$q.loading.show({ message: '正在停止组:' + group.name })
      crossbar.call('sys.ServiceControl.group_stop', [group.name]).then(
        function(res) {
          console.log('Result:', res)
          that.$q.notify({
            message: '成功停止:' + res.toString(),
            closeBtn: true
          })
          that.$q.loading.hide()
        },
        function(err) {
          console.error('Error:', err.error, err.args[0])
          that.$q.loading.hide()
        }
      )
    },
    async openGropHome(group) {
      const that = this
      const crossbar = await that.$store.dispatch('crossbar/get_session')
      crossbar.call('sys.electron.openpath', [group.cwd]).then(
        function(res) {
          console.log('Result:', res)
        },
        function(err) {
          console.error('Error:', err.error, err.args[0])
        }
      )
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
