<script setup>
import { computed, onBeforeUnmount, provide, readonly, ref, watchEffect } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'

const { locale, t } = useI18n()
const route = useRoute()
watchEffect(() => {
  document.title = t(route.meta.title || 'workspace.home') + ' · mml-manager'
  document.documentElement.lang = locale.value === 'zh' ? 'zh-CN' : 'en'
})
const elementLocale = computed(() => (locale.value === 'zh' ? zhCn : en))
const isDark = ref(document.documentElement.classList.contains('dark'))
let themeTransitionTimer

function toggleTheme() {
  const root = document.documentElement
  clearTimeout(themeTransitionTimer)
  root.classList.add('theme-transitioning')
  void root.offsetWidth
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  root.classList.toggle('dark', isDark.value)
  root.style.colorScheme = isDark.value ? 'dark' : 'light'
  themeTransitionTimer = setTimeout(() => {
    root.classList.remove('theme-transitioning')
  }, 280)
}

function toggleLang() {
  locale.value = locale.value === 'zh' ? 'en' : 'zh'
  localStorage.setItem('locale', locale.value)
}

provide('appearance', { isDark: readonly(isDark), toggleTheme, toggleLang })
onBeforeUnmount(() => {
  clearTimeout(themeTransitionTimer)
  document.documentElement.classList.remove('theme-transitioning')
})
</script>

<template>
  <el-config-provider :locale="elementLocale">
    <RouterView v-slot="{ Component }">
      <KeepAlive><component :is="Component" /></KeepAlive>
    </RouterView>
  </el-config-provider>
</template>
