<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { getModule } from '../modules/registry'
import GlobalHeader from '../components/layout/GlobalHeader.vue'
import ModuleSidebar from '../components/layout/ModuleSidebar.vue'
import Breadcrumb from '../components/layout/Breadcrumb.vue'
const route = useRoute()
const currentModule = computed(() => getModule(route.meta.moduleId))
</script>
<template>
  <div class="workspace-shell">
    <GlobalHeader />
    <div class="module-body">
      <ModuleSidebar v-if="currentModule" :module="currentModule" />
      <div class="module-content">
        <Breadcrumb />
        <RouterView v-slot="{ Component }">
          <KeepAlive><component :is="Component" /></KeepAlive>
        </RouterView>
      </div>
    </div>
  </div>
</template>
