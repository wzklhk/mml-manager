<template>
  <aside class="module-sidebar" :class="{ collapsed }">
    <button
      class="sidebar-toggle"
      :aria-expanded="!collapsed"
      :aria-label="t('workspace.toggleMenu')"
      @click="collapsed = !collapsed"
    >
      {{ collapsed ? "☰" : "☰ " + t("workspace.menu") }}
    </button>
    <template v-if="!collapsed">
      <h2>{{ t(module.name) }}</h2>
      <nav :aria-label="t('workspace.functions')">
        <RouterLink v-for="item in visibleMenu" :key="item.id" :to="item.path" class="module-menu-item">
          {{ t(item.title) }}
        </RouterLink>
      </nav>
      <p v-if="module.description" class="sidebar-note">{{ t(module.description) }}</p>
    </template>
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
