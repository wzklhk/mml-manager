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
          <!-- Source: https://github.com/primer/octicons/blob/main/icons/mark-github-16.svg -->
          <svg class="github-mark" viewBox="0 0 16 16" width="20" height="20" fill="currentColor" aria-hidden="true">
            <path
              d="M6.766 11.328c-2.063-.25-3.516-1.734-3.516-3.656 0-.781.281-1.625.75-2.188-.203-.515-.172-1.609.063-2.062.625-.078 1.468.25 1.968.703.594-.187 1.219-.281 1.985-.281.765 0 1.39.094 1.953.265.484-.437 1.344-.765 1.969-.687.218.422.25 1.515.046 2.047.5.593.766 1.39.766 2.203 0 1.922-1.453 3.375-3.547 3.64.531.344.89 1.094.89 1.954v1.625c0 .468.391.734.86.547C13.781 14.359 16 11.53 16 8.03 16 3.61 12.406 0 7.984 0 3.563 0 0 3.61 0 8.031a7.88 7.88 0 0 0 5.172 7.422c.422.156.828-.125.828-.547v-1.25c-.219.094-.5.156-.75.156-1.031 0-1.64-.562-2.078-1.609-.172-.422-.36-.672-.719-.719-.187-.015-.25-.093-.25-.187 0-.188.313-.328.625-.328.453 0 .844.281 1.25.86.313.452.64.655 1.031.655s.641-.14 1-.5c.266-.265.47-.5.657-.656"
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
