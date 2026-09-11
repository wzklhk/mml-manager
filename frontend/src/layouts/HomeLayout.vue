<script setup>
import GlobalHeader from "../components/layout/GlobalHeader.vue";
</script>
<template>
  <div class="workspace-shell">
    <GlobalHeader />
    <main class="home-content"><RouterView /></main>
  </div>
</template>
