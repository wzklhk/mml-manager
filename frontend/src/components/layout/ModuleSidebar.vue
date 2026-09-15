<template>
  <aside class="module-sidebar" :class="{ collapsed }">
    <div class="sidebar-content">
      <p v-if="!collapsed && module.description" class="sidebar-note">{{ t(module.description) }}</p>
      <nav :aria-label="t('workspace.functions')">
        <RouterLink
          v-for="item in visibleMenu"
          :key="item.id"
          :to="item.path"
          class="module-menu-item"
          :title="collapsed ? t(item.title) : undefined"
          :aria-label="collapsed ? t(item.title) : undefined"
        >
          <span class="module-menu-icon" aria-hidden="true">{{ item.icon }}</span>
          <span v-if="!collapsed">{{ t(item.title) }}</span>
        </RouterLink>
      </nav>
    </div>
    <button
      type="button"
      class="sidebar-toggle"
      :aria-expanded="!collapsed"
      :aria-label="collapsed ? t('workspace.expandMenu') : t('workspace.collapseMenu')"
      @click="collapsed = !collapsed"
    >
      <span v-if="!collapsed">{{ t("workspace.collapse") }}</span>
      <svg class="sidebar-toggle-arrow" :class="{ 'is-collapsed': collapsed }" aria-hidden="true" viewBox="0 0 20 20">
        <path d="m7.5 4.5 5.5 5.5-5.5 5.5" />
      </svg>
    </button>
  </aside>
</template>

<script setup>
import { useI18n } from "vue-i18n";
const { t } = useI18n();
import { computed, ref } from "vue";
const props = defineProps({ module: { type: Object, required: true } });
const collapsed = ref(false);
const visibleMenu = computed(() => (props.module.menu || []).filter((item) => item.enabled));
</script>
