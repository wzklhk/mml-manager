<template>
  <el-header class="vue-header">
    <div class="header-left">
      <el-button @click="$emit('menu-select', 'overview')">
        {{ $t("header.table_overview") }}
      </el-button>
      <span v-if="selectedTable" class="selected-table-name">{{ selectedTable }}</span>
    </div>
    <div class="header-right configuration-actions">
      <el-select
        :model-value="activeSnapshotId"
        class="snapshot-select"
        popper-class="snapshot-select-dropdown"
        size="default"
        :disabled="!snapshots.length"
        :title="activeSnapshotLabel"
        :placeholder="$t('header.select_config')"
        @change="$emit('snapshot-change', $event)"
      >
        <el-option v-for="item in snapshots" :key="item.id" :label="snapshotLabel(item)" :value="item.id">
          <span class="snapshot-option-label" :title="snapshotLabel(item)">{{ snapshotLabel(item) }}</span>
        </el-option>
      </el-select>
      <el-button size="default" type="primary" @click="$emit('snapshot-create')">
        {{ $t("header.new_config") }}
      </el-button>
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
          {{ $t("header.import_config") }}
        </el-button>
      </el-upload>
      <el-dropdown :disabled="!canExport" @command="$emit('export-all', $event)">
        <el-button :disabled="!canExport">
          {{ $t("export.configuration") }}
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="mml">MML</el-dropdown-item>
            <el-dropdown-item command="csv">CSV</el-dropdown-item>
            <el-dropdown-item command="xlsx">Excel (.xlsx)</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <el-button size="default" :disabled="!activeSnapshotId" @click="$emit('snapshot-rename', activeSnapshotId)">
        {{ $t("header.rename_config") }}
      </el-button>
      <el-button
        size="default"
        type="danger"
        plain
        :disabled="!activeSnapshotId"
        @click="$emit('snapshot-delete', activeSnapshotId)"
      >
        {{ $t("header.delete_config") }}
      </el-button>
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
    canExport: { type: Boolean, default: false },
  },
  computed: {
    activeSnapshotLabel() {
      const activeSnapshot = this.snapshots.find((item) => item.id === this.activeSnapshotId);
      return activeSnapshot ? this.snapshotLabel(activeSnapshot) : "";
    },
    uploadUrl() {
      return apiUrl("/api/import-mml");
    },
  },
  methods: {
    snapshotLabel(item) {
      return item.name || item.network_element || "";
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
  flex: 0 1 220px;
  min-width: 0;
  width: 220px;
  max-width: 100%;
}
.snapshot-select :deep(.el-select__wrapper),
.snapshot-select :deep(.el-select__selection) {
  min-width: 0;
}
.snapshot-select :deep(.el-select__selected-item) {
  display: block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
:global(.snapshot-select-dropdown) {
  width: min(360px, calc(100vw - 32px)) !important;
  max-width: calc(100vw - 32px);
}
:global(.snapshot-select-dropdown .el-select-dropdown__item) {
  padding-right: 8px;
}
.snapshot-option-label {
  display: block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.header-upload {
  display: inline-flex;
}
</style>
