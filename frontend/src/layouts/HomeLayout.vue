<script setup>
import GlobalHeader from "../components/layout/GlobalHeader.vue";
import AppFooter from "../components/AppFooter.vue";
</script>
<template>
  <div class="workspace-shell">
    <GlobalHeader />
    <main class="home-content">
      <RouterView />
      <AppFooter />
    </main>
  </div>
</template>
