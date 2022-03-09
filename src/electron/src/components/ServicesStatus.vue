<template>
  <q-dialog
    ref="dialog"
    :maximized="maximizedToggle"
    @hide="onDialogHide"
  >
    <q-layout view="lHh Lpr lFf" container>
      <q-header class="bg-primary">
        <q-bar class="bg-primary text-white">
          <span>
            服务管理器
          </span>
          <q-space />
          <q-btn dense round flat icon="minimize" :disable="!maximizedToggle" @click="maximizedToggle = false">
            <q-tooltip v-if="maximizedToggle">最小化</q-tooltip>
          </q-btn>
          <q-btn dense round flat icon="crop_square" :disable="maximizedToggle" @click="maximizedToggle = true">
            <q-tooltip v-if="!maximizedToggle">最大化</q-tooltip>
          </q-btn>
          <q-btn v-close-popup round dense flat icon="close">
            <q-tooltip>关闭</q-tooltip>
          </q-btn>
        </q-bar>
      </q-header>

      <q-page-container>
        <q-page>

          <q-card square style="font-size: 12px">
            <q-card-section class="q-pa-xs  text-grey-9">
              <div class="row q-col-gutter-xs">
                <div v-for="service in status" :key="service.full_name" class="col-xs-12 col-md-6" style="min-width:250px;">
                  <q-card flat bordered>
                    <q-card-section class="q-ma-none q-pa-xs">
                      <q-item class="q-ma-none q-pa-none">
                        <q-item-section>
                          <q-item-label>
                            <span class="text-h6">{{ service.full_name }}</span>

                          </q-item-label>
                          <q-item-label caption>
                            <q-spinner-dots
                              v-if="service.status==='starting'"
                              color="green"
                              size="1.5em"
                            />
                            <q-icon v-else name="lens" :color="service.status==='running'?'green':service.status==='starting'?'yellow':'red'" />
                            <q-icon name="check" />
                            {{ service.last_at }}
                          </q-item-label>
                        </q-item-section>
                        <q-item-section avatar>
                          <q-btn flat icon="notes" @click="showConsole(service)">
                            <q-tooltip>查看日志</q-tooltip>
                          </q-btn>
                        </q-item-section>
                      </q-item>
                    </q-card-section>
                    <q-separator v-if="service.description" />
                    <q-card-section v-if="service.description" class="q-ma-none q-pa-xs">
                      {{ service.description }}
                    </q-card-section>
                    <q-separator v-if="service.urls&&service.urls.length>0" />
                    <q-card-section v-if="service.urls&&service.urls.length>0" class="q-ma-none q-pa-xs">
                      <q-list dense class="q-ma-none q-pa-none">
                        <q-item v-for="(url, i) in service.urls" :key="i" class="q-ma-none q-pa-none">
                          <q-item-section>
                            <q-item-label>{{ url.title }}</q-item-label>
                            <q-item-label caption lines="2">
                              <a :href="url.url" target="_blank">{{ url.url }}</a>
                              <q-btn flat round size="xs" icon="content_copy" @click="doCopy(url.url)" />
                            </q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-btn flat size="sm" round icon="fast_forward" />
                          </q-item-section>
                        </q-item>
                      </q-list>
                    </q-card-section>
                    <q-separator />
                    <q-card-actions>
                      <q-btn :disable="service.status==='running'||service.status==='starting'" @click="startService(service)">启动</q-btn>
                      <q-btn :disable="service.status==='stop'||!service.status" @click="stopService(service)">停止</q-btn>
                    </q-card-actions>
                  </q-card>
                </div>
              </div>
            </q-card-section>
          </q-card>
          <q-page-scroller position="bottom-right" :scroll-offset="150" :offset="[18, 18]">
            <q-btn fab icon="keyboard_arrow_up" color="primary" />
          </q-page-scroller>
        </q-page>
      </q-page-container>
    </q-layout>
  </q-dialog>
</template>

<script>
import { mapGetters } from 'vuex'
import EventConsole from 'components/EventConsole.vue'
import { QSpinnerGears } from 'quasar'
export default {
  props: {
    status: {
      type: Array,
      required: true
    },
    maximized: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      maximizedToggle: this.maximized
    }
  },
  computed: {
    ...mapGetters('crossbar', [
      'evtCoreServiceOut',
      'evtCoreServicePrint'
    ])
  },
  methods: {
    show() {
      this.$refs.dialog.show()
    },
    hide() {
      this.$refs.dialog.hide()
    },
    onDialogHide() {
      this.$emit('hide')
    },
    onOKClick() {
      this.$emit('ok')
      this.hide()
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
    showConsole(service) {
      this.$q.dialog({
        component: EventConsole,
        parent: this, // becomes child of this Vue node
        events: this.evtCoreServicePrint,
        maximized: true,
        title: 'Service事件查看器',
        fromJson: (v) => v.msg,
        group: {
          selected:
            service.full_name,
          nameField: 'name',
          groups: this.status.map((v) => {
            return v.full_name
          })
        }
      })
    }
  }
}
</script>
