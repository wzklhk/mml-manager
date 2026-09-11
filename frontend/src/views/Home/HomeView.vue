<script setup>
import { useI18n } from "vue-i18n";
const { t } = useI18n();
import { RouterLink } from "vue-router";
import { enabledModules, moduleGroups } from "../../modules/registry";
const enabledCount = enabledModules.length;
</script>
<template>
  <div class="workspace-home">
    <div class="home-intro">
      <div>
        <p class="home-eyebrow">NETWORK OPERATIONS</p>
        <h1>{{ t("workspace.home") }}</h1>
        <p>{{ t("workspace.intro") }}</p>
      </div>
      <span class="home-status"><span></span>{{ t("workspace.availableCount", { count: enabledCount }) }}</span>
    </div>
    <section v-for="group in moduleGroups" :key="group.name" class="home-group">
      <h2>{{ t(group.name) }}</h2>
      <div class="module-card-grid">
        <component
          :is="RouterLink"
          v-for="module in group.modules"
          :key="module.id"
          :to="module.path"
          class="module-card"
        >
          <div class="module-card-top">
            <span class="module-icon" aria-hidden="true">{{ module.icon }}</span>
            <span class="module-status">{{ t("workspace.available") }}</span>
          </div>
          <h3>{{ t(module.name) }}</h3>
          <span class="module-code">{{ module.code }}</span>
          <p>{{ t(module.description) }}</p>
          <span class="module-card-action">{{ t("workspace.enter") }}</span>
        </component>
      </div>
    </section>
  </div>
</template>
