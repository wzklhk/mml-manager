<script setup>
import { RouterLink } from 'vue-router'
import { appModules, moduleGroups } from '../../modules/registry'
const enabledCount = appModules.filter(module => module.enabled).length
</script>
<template>
  <div class="workspace-home">
    <div class="home-intro">
      <div><p class="home-eyebrow">NETWORK OPERATIONS</p><h1>工作台</h1><p>从配置管理出发，连接网络规划、资源与运维。</p></div>
      <span class="home-status"><span></span>{{ enabledCount }} 个模块可用</span>
    </div>
    <section v-for="group in moduleGroups" :key="group.name" class="home-group">
      <h2>{{ group.name }}</h2>
      <div class="module-card-grid">
        <component :is="module.enabled ? RouterLink : 'div'" v-for="module in group.modules" :key="module.id"
          :to="module.enabled ? module.path : undefined" class="module-card"
          :class="{ 'is-disabled': !module.enabled }" :aria-disabled="!module.enabled">
          <div class="module-card-top"><span class="module-icon" aria-hidden="true">{{ module.icon }}</span>
            <span class="module-status">{{ module.enabled ? '可用' : '开发中' }}</span></div>
          <h3>{{ module.name }}</h3><span class="module-code">{{ module.code }}</span>
          <p>{{ module.description }}</p>
          <span class="module-card-action">{{ module.enabled ? '进入模块 →' : 'Coming Soon' }}</span>
        </component>
      </div>
    </section>
  </div>
</template>
