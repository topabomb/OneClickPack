<template>
  <q-dialog
    ref="dialog"
    persistent
    :maximized="maximizedToggle"
    @hide="onDialogHide"
    @show="onDialogShow"
  >
    <q-layout view="Lhh lpR fff" container class="bg-white">
      <q-header class="bg-primary">
        <q-bar class="bg-primary text-white">
          <span>
            {{ title }}
          </span>
          <q-space />
          <q-btn dense flat round icon="minimize" :disable="!maximizedToggle" @click="maximizedToggle = false">
            <q-tooltip v-if="maximizedToggle">最小化</q-tooltip>
          </q-btn>
          <q-btn dense flat round icon="crop_square" :disable="maximizedToggle" @click="maximizedToggle = true">
            <q-tooltip v-if="!maximizedToggle">最大化</q-tooltip>
          </q-btn>
          <q-btn v-close-popup round dense flat icon="close">
            <q-tooltip>关闭</q-tooltip>
          </q-btn>
        </q-bar>
      </q-header>
      <q-drawer v-model="drawer" side="right" bordered :width="180" :breakpoint="190" content-class="bg-grey-3 q-pa-sm">
        <q-card flat bordered>
          <q-card-section class="q-pa-xs">
            <div class="text-h6">分组</div>
          </q-card-section>
          <q-separator inset />
          <q-card-section class="q-pa-xs">
            <q-list dense>
              <q-item v-for="(g,i) in group_options" :key="i" v-ripple tag="label" dense>
                <q-item-section>
                  <q-radio v-model="selectedGroup" size="xs" :val="g.value" color="teal" dense />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ g.label }}</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
          <q-separator />
          <q-card-section class="q-pa-xs">
            <div class="text-h6">选项</div>
          </q-card-section>
          <q-separator inset />
          <q-card-section class="q-pa-xs">
            <q-toggle v-model="enabled_autoscrool" size="sm" dense checked-icon="check" label="滚屏" />

          </q-card-section>
          <q-card-section class="q-pa-xs">
            <q-btn rounded color="primary" size="sm" icon="clear" label="清空" @click="cleanEvent()" />
          </q-card-section>
          <q-separator />
          <q-card-section class="q-pa-xs">
            <div class="text-h6">高亮</div>
          </q-card-section>
          <q-separator inset />
          <q-card-section class="q-pa-xs">
            <q-input v-model="searchText" dense label="正则表达式">
              <template v-slot:append>
                <q-btn flat round size="xs" icon="close" @click="searchText=null" />
              </template>
            </q-input>
          </q-card-section>
          <q-card-section class="q-pa-xs">
            <q-input v-model="searchColor" dense label="背景颜色">
              <template v-slot:append>
                <q-icon name="colorize">
                  <q-popup-proxy>
                    <q-color
                      v-model="searchColor"
                      default-view="palette"
                    />
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>
          </q-card-section>
          <q-separator />

        </q-card>
      </q-drawer>
      <q-page-container>
        <q-page style="font-size: 12px">
          <q-virtual-scroll
            ref="virtualListRef"
            class="virtualList"
            :items="filter_events"
            separator
            dense
            :virtual-scroll-slice-size="200"
          >
            <template v-slot="{ item, index }">
              <q-item
                v-if="is_highlight(item)"
                :key="index"
                dense
                class="text-white q-my-none q-py-none"
                :style="'background-color:'+searchColor"
              >
                <q-item-section>
                  <q-item-label>
                    #{{ index }}- {{ item }}
                  </q-item-label>
                </q-item-section>
              </q-item>
              <q-item
                v-else
                :key="index"
                dense
                class="q-ma-none q-py-none"
              >
                <q-item-section>
                  <q-item-label>
                    #{{ index }}- {{ item }}
                  </q-item-label>
                </q-item-section>
              </q-item>
            </template>
          </q-virtual-scroll>
        </q-page>
      </q-page-container>
    </q-layout>
  </q-dialog>
</template>

<script>
export default {
  props: {
    events: {
      type: Array,
      required: true
    },
    maximized: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      default: '事件查看器'
    },
    pattern: {
      type: String,
      default: null
    },
    fromJson: {
      type: Function,
      default: null
    },
    group: {
      type: Object,
      default: () => {
        return {
          selected: null,
          nameField: null,
          groups: null
        }
      }
    }
  },
  data() {
    return {
      drawer: true,
      maximizedToggle: this.maximized,
      enabled_autoscrool: true,
      searchText: this.pattern,
      searchColor: '#ff9933',
      selectedGroup: this.group.selected
    }
  },
  computed: {
    group_options: function() {
      return this.group.groups ? this.group.groups.map(v => {
        return {
          label: v,
          value: v
        }
      }) : [{ label: '全部', value: null }]
    },
    filter_events: function() {
      if (this.selectedGroup && this.fromJson) {
        return this.events.filter(v => {
          return v.v[this.group.nameField] === this.selectedGroup
        }).map(v => this.fromJson ? this.fromJson(v.v) : v.msg)
      } else return this.events.map(v => this.fromJson ? this.fromJson(v) : v)
    }
  },
  watch: {
    events: {
      handler(val, old) {
        if (this.enabled_autoscrool && this.$refs.virtualListRef) this.$refs.virtualListRef.scrollTo(this.filter_events.length - 1)
      },
      deep: true
    }

  },
  mounted() {

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
    onDialogShow() {
      this.$refs.virtualListRef.scrollTo(this.events.length - 1)
    },
    is_highlight(val) {
      if (this.searchText) {
        return new RegExp(this.searchText).test(val)
      }
    },
    cleanEvent() {
      const that = this
      that.$q.dialog({
        title: '暂未实现',
        message: '暂未开放该功能！因为在组件中无法操作vuex'
      })
      return
      if (this.selectedGroup && this.fromJson) {
        const length = this.events.length
        for (let i = 0; i < length; i++) {
        // 删除数组中所有的1
          if (this.events[i] && this.events[i][this.group.nameField] === this.selectedGroup) {
            this.events.splice(i, 1)
            // 重置i，否则i会跳一位
            i--
          }
        }
      } else {
        this.events.splice(0, this.events.length)
      }
    }
  }
}
</script>
<style scoped>
.virtualList{
  max-height: calc(100vh - 40px);
}
</style>
