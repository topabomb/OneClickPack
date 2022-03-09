<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <MainMenu :status="arrCoreServiceStatus" />
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>

    <q-footer elevated class="bg-grey-9 text-white">
      <StatusBar
        :status="arrCoreServiceStatus"
        :out-events="evtCoreServiceOut"
        :print-events="evtCoreServicePrint"
        :connected="connected&&api_ready"
      />
    </q-footer>
  </q-layout>
</template>
<script>
import { mapGetters } from 'vuex'
import MainMenu from 'components/MainMenu.vue'
import StatusBar from 'components/StatusBar.vue'
export default {
  name: 'MainLayout',
  components: { MainMenu, StatusBar },
  data() {
    return {
    }
  },
  computed: {
    ...mapGetters('crossbar', [
      'evtCoreServiceOut',
      'evtCoreServicePrint',
      'arrCoreServiceStatus',
      'connected',
      'api_ready'
    ])
  },

  methods: {

  }
}
</script>

