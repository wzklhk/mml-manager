<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { getModule } from '../../modules/registry'
const route = useRoute()
const currentModule = computed(() => getModule(route.meta.moduleId))
</script>
<template>
  <el-breadcrumb separator="/" class="workspace-breadcrumb">
    <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
    <el-breadcrumb-item v-if="currentModule" :to="{ path: currentModule.path }">{{ currentModule.name }}</el-breadcrumb-item>
    <el-breadcrumb-item>{{ route.meta.title }}</el-breadcrumb-item>
  </el-breadcrumb>
</template>
