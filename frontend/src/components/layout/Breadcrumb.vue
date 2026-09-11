<template>
  <el-breadcrumb separator="/" class="workspace-breadcrumb">
    <el-breadcrumb-item :to="{ path: '/' }">{{ t("workspace.homepage") }}</el-breadcrumb-item>
    <el-breadcrumb-item v-if="currentModule" :to="{ path: currentModule.path }">{{
      t(currentModule.name)
    }}</el-breadcrumb-item>
    <el-breadcrumb-item>{{ t(route.meta.title || "workspace.home") }}</el-breadcrumb-item>
  </el-breadcrumb>
</template>

<script setup>
import { useI18n } from "vue-i18n";
const { t } = useI18n();
import { computed } from "vue";
import { useRoute } from "vue-router";
import { getModule } from "../../modules/registry";
const route = useRoute();
const currentModule = computed(() => getModule(route.meta.moduleId));
</script>
