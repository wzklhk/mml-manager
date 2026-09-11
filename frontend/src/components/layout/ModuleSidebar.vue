<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
import { ref } from 'vue'
defineProps({ module: { type: Object, required: true } })
const collapsed = ref(false)
</script>
<template>
  <aside class="module-sidebar" :class="{ collapsed }">
    <button
      class="sidebar-toggle"
      :aria-expanded="!collapsed"
      :aria-label="t('workspace.toggleMenu')"
      @click="collapsed = !collapsed"
    >
      {{ collapsed ? '☰' : '☰ ' + t('workspace.menu') }}
    </button>
    <template v-if="!collapsed">
      <h2>{{ t(module.name) }}</h2>
      <nav :aria-label="t('workspace.functions')">
        <template v-for="item in module.menu || []" :key="item.id">
          <RouterLink v-if="item.enabled" :to="item.path" class="module-menu-item">{{ t(item.title) }}</RouterLink>
          <button v-else class="module-menu-item" disabled>
            {{ t(item.title) }}<small>{{ t('workspace.soon') }}</small>
          </button>
        </template>
      </nav>
      <p v-if="module.description" class="sidebar-note">{{ t(module.description) }}</p>
    </template>
  </aside>
</template>
