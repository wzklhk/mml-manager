<template>
  <header class="global-header">
    <RouterLink to="/" class="workspace-brand"><span class="brand-symbol">m</span>mml-manager</RouterLink>
    <ModuleSwitcher />
    <span class="current-module">{{ currentName }}</span>
    <div class="global-header-end">
      <el-input
        class="global-search"
        :placeholder="t('workspace.search')"
        :aria-label="t('workspace.search')"
        disabled
      />
      <el-button disabled :title="t('workspace.settingsSoon')">{{ t("workspace.settings") }}</el-button>
      <!-- 语言切换 -->
      <button type="button" class="header-icon-btn lang-btn" aria-label="中文 / English" @click="toggleLang()">
        {{ $i18n.locale === "zh" ? "EN" : "中文" }}
      </button>

      <!-- 主题切换 -->
      <button
        type="button"
        class="header-icon-btn"
        @click="toggleTheme()"
        :title="isDark ? $t('header.theme_light') : $t('header.theme_dark')"
        :aria-label="isDark ? $t('header.theme_light') : $t('header.theme_dark')"
        :aria-pressed="isDark"
      >
        <Transition name="theme-icon" mode="out-in">
          <svg v-if="isDark" key="sun" viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path
              d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75V21a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM7.758 17.303a.75.75 0 00-1.061-1.06l-1.591 1.59a.75.75 0 001.06 1.061l1.591-1.59zM6 12a.75.75 0 01-.75.75H3a.75.75 0 010-1.5h2.25A.75.75 0 016 12zM6.697 7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 00-1.061 1.06l1.59 1.591z"
            />
          </svg>
          <svg v-else key="moon" viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path
              d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z"
            />
          </svg>
        </Transition>
      </button>

      <!-- GitHub -->
      <a
        href="https://github.com/wzklhk/mml-manager"
        target="_blank"
        rel="noopener noreferrer"
        class="header-icon-btn github-link"
        title="GitHub"
      >
        <svg viewBox="0 0 16 16" width="18" height="18" fill="currentColor">
          <path
            d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"
          />
        </svg>
      </a>
    </div>
  </header>
</template>

<script setup>
import { useI18n } from "vue-i18n";
const { t } = useI18n();
import { computed, inject } from "vue";
import { useRoute } from "vue-router";
import { getModule } from "../../modules/registry";
import ModuleSwitcher from "./ModuleSwitcher.vue";
const { isDark, toggleTheme, toggleLang } = inject("appearance");
const route = useRoute();
const currentName = computed(() => t(getModule(route.meta.moduleId)?.name || "workspace.home"));
</script>

<style scoped>
/* ---- Icon-style buttons ---- */
.header-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--header-text-muted);
  cursor: pointer;
  transition:
    color 0.2s,
    background 0.2s;
  text-decoration: none;
}
.header-icon-btn:hover {
  color: var(--header-text-active);
  background: var(--header-btn-bg-hover);
}
.theme-icon-enter-active,
.theme-icon-leave-active {
  transition:
    opacity 0.12s ease,
    transform 0.12s ease;
}
.theme-icon-enter-from {
  opacity: 0;
  transform: rotate(-45deg) scale(0.75);
}
.theme-icon-leave-to {
  opacity: 0;
  transform: rotate(45deg) scale(0.75);
}
.lang-btn {
  width: auto;
  padding: 0 8px;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.3px;
}
</style>
