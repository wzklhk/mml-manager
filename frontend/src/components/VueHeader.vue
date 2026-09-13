<template>
  <el-header class="vue-header">
    <div class="header-left">
      <el-button @click="$emit('menu-select', 'overview')">{{ $t("header.table_overview") }}</el-button>
      <el-select
        v-if="snapshots.length"
        :model-value="activeSnapshotId"
        class="snapshot-select"
        size="default"
        :placeholder="$t('header.select_config')"
        @change="$emit('snapshot-change', $event)"
      >
        <el-option v-for="item in snapshots" :key="item.id" :label="snapshotLabel(item)" :value="item.id" />
      </el-select>
      <el-button
        v-if="activeSnapshotId"
        type="danger"
        plain
        size="default"
        @click="$emit('snapshot-delete', activeSnapshotId)"
      >
        {{ $t("header.delete_config") }}
      </el-button>
      <span v-if="selectedTable" class="selected-table-name">{{ selectedTable }}</span>
    </div>
    <div class="header-right">
      <el-button size="default" @click="$emit('snapshot-create')">{{ $t("header.new_config") }}</el-button>
      <el-button size="default" @click="$emit('compare')">{{ $t("header.compare_mml") }}</el-button>
      <el-upload
        class="header-upload"
        :action="uploadUrl"
        @success="(r) => $emit('upload-success', r)"
        @error="(e) => $emit('upload-error', e)"
        :before-upload="beforeUpload"
        accept=".mml,.txt,.csv,.xlsx"
        :show-file-list="false"
      >
        <el-button size="default" type="primary">
          {{ $t("header.import_data") }}
        </el-button>
      </el-upload>
    </div>
  </el-header>
</template>

<script>
import { apiUrl } from "../api/client";

export default {
  name: "VueHeader",
  props: {
    menuActive: { type: String, default: "overview" },
    selectedTable: { type: String, default: "" },
    snapshots: { type: Array, default: () => [] },
    activeSnapshotId: { type: String, default: "" },
  },
  computed: {
    uploadUrl() {
      return apiUrl("/api/import-mml");
    },
  },
  methods: {
    snapshotLabel(item) {
      const importedAt = item.loaded_at ? item.loaded_at.replace("T", " ").slice(0, 19) : "";
      const names = item.name && item.name !== item.network_element ? [item.network_element, item.name] : [item.name];
      return [...names, importedAt].filter(Boolean).join(" · ");
    },
    beforeUpload(file) {
      if (![".mml", ".txt", ".csv", ".xlsx"].some((ext) => file.name.toLowerCase().endsWith(ext))) {
        this.$message.error(this.$t("header.only_import_file"));
        return false;
      }
      this.$emit("upload-start");
      return true;
    },
  },
};
</script>

<style scoped>
.vue-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 20px;
  height: auto;
  min-height: 64px;
  flex-shrink: 0;
  background: var(--header-bg);
  border-bottom: 1px solid var(--border-color);
}
.header-left,
.header-right {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  min-width: 0;
}
.header-right {
  margin-left: auto;
}
.selected-table-name {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  color: var(--text-secondary);
}
.snapshot-select {
  width: 220px;
  max-width: 100%;
}
.header-upload {
  display: inline-flex;
}
</style>
