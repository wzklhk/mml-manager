<template>
  <header class="global-header">
    <div class="global-header-inner">
      <RouterLink to="/" class="workspace-brand" aria-label="mml-manager">
        <svg class="brand-logo" viewBox="0 0 32 28" aria-hidden="true">
          <path fill="#42b883" d="M1 1h7l8 14 8-14h7L16 27z" />
          <path fill="#35495e" d="M8 1h5l3 5.3L19 1h5l-8 14z" />
        </svg>
        <span>mml-manager</span>
      </RouterLink>

      <ModuleSwitcher />

      <nav class="header-nav" :aria-label="$t('workspace.functions')">
        <RouterLink to="/" class="header-nav-link">{{ $t("workspace.home") }}</RouterLink>
        <span v-if="currentModule" class="header-nav-link current-module" aria-current="page">{{ currentName }}</span>
      </nav>

      <div class="global-header-end">
        <el-dropdown trigger="hover" @command="setLang">
          <button
            type="button"
            class="header-icon-btn lang-btn"
            :title="$t('header.language')"
            :aria-label="$t('header.language')"
            aria-haspopup="menu"
          >
            <span class="header-emoji" aria-hidden="true">🌐</span>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="zh" :disabled="$i18n.locale === 'zh'">中文</el-dropdown-item>
              <el-dropdown-item command="en" :disabled="$i18n.locale === 'en'">English</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-dropdown trigger="hover" @command="setTheme">
          <button
            type="button"
            class="header-icon-btn"
            :title="$t('header.theme')"
            :aria-label="$t('header.theme')"
            aria-haspopup="menu"
          >
            <span class="header-emoji" aria-hidden="true">👕</span>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="theme in themes"
                :key="theme.id"
                :command="theme.id"
                :class="{ 'theme-option-selected': theme.id === currentTheme }"
              >
                <span class="theme-option-icon" aria-hidden="true">{{ theme.icon }}</span>
                <span>{{ $t(theme.labelKey) }}</span>
                <span v-if="theme.id === currentTheme" class="theme-option-check" aria-hidden="true">✓</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <a
          href="https://github.com/wzklhk/mml-manager"
          target="_blank"
          rel="noopener noreferrer"
          class="header-icon-btn github-link"
          title="GitHub"
          aria-label="GitHub"
        >
          <svg
            class="github-mark"
            viewBox="-0.5 -0.5 17 17"
            width="19"
            height="19"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8z"
            />
          </svg>
        </a>
      </div>
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
const { currentTheme, themes, setTheme, setLang } = inject("appearance");
const route = useRoute();
const currentModule = computed(() => getModule(route.meta.moduleId));
const currentName = computed(() => t(currentModule.value?.name || "workspace.home"));
</script>

<style scoped>
.header-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 6px;
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
.lang-btn,
.header-emoji {
  font-size: 18px;
}
.header-emoji {
  line-height: 1;
}
.theme-option-icon {
  width: 24px;
  font-size: 16px;
}
.theme-option-check {
  margin-left: auto;
  padding-left: 20px;
  color: var(--el-color-primary);
  font-weight: 700;
}
:global(.theme-option-selected) {
  color: var(--el-color-primary);
  font-weight: 600;
}
.github-mark {
  display: block;
  overflow: visible;
}
</style>
