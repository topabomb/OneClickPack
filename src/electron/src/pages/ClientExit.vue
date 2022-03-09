<template>
  <div class="fit row justify-center">
    <q-item class="q-ma-xl">
      <q-spinner-hourglass color="primary" size="xl" />
      <q-item-section>
        <q-item-label>清理后退出</q-item-label>
        <q-item-label caption>正在退出已启动的服务...</q-item-label>
        <q-item-label>
          <q-badge
            v-for="(item, index) in running_services"
            :key="index"
            class="q-ma-xs"
            outline
            color="secondary"
            :label="item.name"
          />
        </q-item-label>
      </q-item-section>
    </q-item>
  </div>
</template>
<script>
import { mapGetters } from 'vuex'
export default {
  data() {
    return {}
  },
  computed: {
    ...mapGetters('crossbar', ['arrCoreServiceStatus']),
    running_services: function() {
      return this.arrCoreServiceStatus.filter(
        (x) => x.status === 'running' || x.status === 'starting'
      )
    }
  },
  mounted: async function() {
    // await this.closeRunning();
  },
  methods: {
    async closeRunning() {
      const that = this
      const proc = async() => {
        try {
          const crossbar = await that.$store.dispatch('crossbar/get_session')
          if (!crossbar) throw 'crossbar/get_session 未获取到有效的连接'
          const resp = await crossbar.call('sys.ServiceControl.running_stop')
          that.groups = resp
          console.log('running_stop success:', resp)
        } catch (err) {
          console.error('running_stop error:', err)
          setTimeout(proc, 1000 * 1)
        }
      }
      await proc()
    }
  }
}
</script>
