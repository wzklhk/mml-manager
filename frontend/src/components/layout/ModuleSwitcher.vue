<template>
  <el-popover
    v-model:visible="visible"
    trigger="click"
    placement="bottom-start"
    :width="420"
    popper-class="module-switcher"
  >
    <template #reference>
      <button class="switcher-trigger" :aria-label="t('workspace.switcher')" :aria-expanded="visible">
        <span aria-hidden="true">🧩</span>
        <span class="switcher-trigger-label">{{ t("workspace.switcher") }}</span>
      </button>
    </template>
    <nav :aria-label="t('workspace.globalSwitcher')" @keydown.esc="visible = false">
      <button class="switcher-home" @click="navigate('/')">🏠 {{ t("workspace.home") }}</button>
      <section v-for="group in moduleGroups" :key="group.name" class="switcher-group">
        <h3>{{ t(group.name) }}</h3>
        <div class="switcher-grid">
          <button v-for="module in group.modules" :key="module.id" @click="navigate(module.path)">
            <span>{{ t(module.name) }}</span>
          </button>
        </div>
      </section>
    </nav>
  </el-popover>
</template>

<script setup>
import { useI18n } from "vue-i18n";
const { t } = useI18n();
import { ref } from "vue";
import { useRouter } from "vue-router";
import { moduleGroups } from "../../modules/registry";
const visible = ref(false);
const router = useRouter();
function navigate(path) {
  visible.value = false;
  router.push(path);
}
</script>
