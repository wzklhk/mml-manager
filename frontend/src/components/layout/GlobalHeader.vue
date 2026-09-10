<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { getModule } from '../../modules/registry'
import ModuleSwitcher from './ModuleSwitcher.vue'
const route = useRoute()
const currentName = computed(() => getModule(route.meta.moduleId)?.name || '工作台')
</script>
<template>
  <header class="global-header">
    <RouterLink to="/" class="workspace-brand"><span class="brand-symbol">m</span>mml-manager</RouterLink>
    <ModuleSwitcher />
    <span class="current-module">{{ currentName }}</span>
    <div class="global-header-end">
      <el-input class="global-search" placeholder="全局搜索 · 开发中" aria-label="全局搜索（开发中）" disabled />
      <el-button disabled title="系统设置开发中">设置</el-button>
      <span class="workspace-user">本地工作台</span>
    </div>
  </header>
</template>
