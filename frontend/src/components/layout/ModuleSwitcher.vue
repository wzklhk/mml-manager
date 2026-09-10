<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { moduleGroups } from '../../modules/registry'
const visible = ref(false)
const router = useRouter()
function navigate(path) {
  visible.value = false
  router.push(path)
}
</script>
<template>
  <el-popover v-model:visible="visible" trigger="click" placement="bottom-start" :width="420" popper-class="module-switcher">
    <template #reference>
      <button class="switcher-trigger" aria-label="模块切换" :aria-expanded="visible">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
          <path d="M3 3h4v4H3zm7 0h4v4h-4zm7 0h4v4h-4zM3 10h4v4H3zm7 0h4v4h-4zm7 0h4v4h-4zM3 17h4v4H3zm7 0h4v4h-4zm7 0h4v4h-4z" />
        </svg>
      </button>
    </template>
    <nav aria-label="全局模块切换" @keydown.esc="visible = false">
      <button class="switcher-home" @click="navigate('/')">⌂ 工作台</button>
      <section v-for="group in moduleGroups" :key="group.name" class="switcher-group">
        <h3>{{ group.name }}</h3>
        <div class="switcher-grid">
          <button v-for="module in group.modules" :key="module.id" :disabled="!module.enabled"
            @click="navigate(module.path)">
            <span>{{ module.name }}</span><small v-if="!module.enabled">开发中</small>
          </button>
        </div>
      </section>
    </nav>
  </el-popover>
</template>
