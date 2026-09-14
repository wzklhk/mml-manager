<template>
  <el-config-provider :locale="elementLocale">
    <RouterView v-slot="{ Component }">
      <KeepAlive><component :is="Component" /></KeepAlive>
    </RouterView>
  </el-config-provider>
</template>

<script setup>
import { computed, provide, readonly, ref, watchEffect } from "vue";
import { useRoute } from "vue-router";
import { useI18n } from "vue-i18n";
import zhCn from "element-plus/dist/locale/zh-cn.mjs";
import en from "element-plus/dist/locale/en.mjs";

const { locale, t } = useI18n();
const route = useRoute();
watchEffect(() => {
  document.title = t(route.meta.title || "workspace.home") + " · mml-manager";
  document.documentElement.lang = locale.value === "zh" ? "zh-CN" : "en";
});
const elementLocale = computed(() => (locale.value === "zh" ? zhCn : en));
const isDark = ref(document.documentElement.classList.contains("dark"));
let themeSwitchFrame;

function toggleTheme() {
  const root = document.documentElement;
  const nextIsDark = !isDark.value;

  window.cancelAnimationFrame(themeSwitchFrame);
  root.classList.add("theme-switching");
  isDark.value = nextIsDark;
  localStorage.setItem("theme", nextIsDark ? "dark" : "light");
  root.classList.toggle("dark", nextIsDark);
  root.style.colorScheme = nextIsDark ? "dark" : "light";

  // Keep transitions disabled until the new theme has been painted once.
  themeSwitchFrame = window.requestAnimationFrame(() => {
    themeSwitchFrame = window.requestAnimationFrame(() => {
      root.classList.remove("theme-switching");
    });
  });
}

function setLang(nextLocale) {
  if (!Object.hasOwn({ zh: true, en: true }, nextLocale)) return;
  locale.value = nextLocale;
  localStorage.setItem("locale", nextLocale);
}

provide("appearance", { isDark: readonly(isDark), toggleTheme, setLang });
</script>
