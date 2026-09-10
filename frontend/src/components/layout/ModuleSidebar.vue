<script setup>
import { ref } from 'vue'
defineProps({ module: { type: Object, required: true } })
const collapsed = ref(false)
</script>
<template>
  <aside class="module-sidebar" :class="{ collapsed }">
    <button class="sidebar-toggle" :aria-expanded="!collapsed" aria-label="折叠或展开模块菜单" @click="collapsed = !collapsed">
      {{ collapsed ? '☰' : '☰ 模块菜单' }}
    </button>
    <template v-if="!collapsed">
      <h2>{{ module.name }}</h2>
      <nav aria-label="当前模块功能">
        <template v-for="item in module.menu || []" :key="item.id">
          <RouterLink v-if="item.enabled" :to="item.path" class="module-menu-item">{{ item.title }}</RouterLink>
          <button v-else class="module-menu-item" disabled>{{ item.title }}<small>开发中</small></button>
        </template>
      </nav>
      <p v-if="module.description" class="sidebar-note">{{ module.description }}</p>
    </template>
  </aside>
</template>
