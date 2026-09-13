<template>
  <el-dialog
    class="mml-ui"
    :model-value="visible"
    :title="$t('export.preview_title')"
    width="min(1080px, 94vw)"
    :close-on-click-modal="!loading"
    :close-on-press-escape="!loading"
    destroy-on-close
    @close="close"
  >
    <el-descriptions :column="3" border class="export-summary">
      <el-descriptions-item :label="$t('export.format')">{{ format.toUpperCase() }}</el-descriptions-item>
      <el-descriptions-item :label="$t('export.scope')">
        {{ scope === "selected" ? $t("export.scope_selected") : $t("export.scope_all") }}
      </el-descriptions-item>
      <el-descriptions-item :label="$t('export.count')">{{ count }}</el-descriptions-item>
    </el-descriptions>

    <template v-if="scope === 'selected'">
      <p class="preview-hint">
        {{ $t("export.selected_preview_hint", { count }) }}
        <span v-if="hiddenRowCount">{{ $t("export.preview_limited", { count: previewLimit }) }}</span>
      </p>
      <el-table :data="previewRows" row-key="id" border stripe max-height="440">
        <el-table-column prop="id" label="ID" width="80" fixed="left" />
        <el-table-column
          v-for="column in columns"
          :key="column"
          :label="column"
          :prop="`config_data.${column}`"
          min-width="140"
        >
          <template #default="scope">
            <span class="cell-value">{{ displayValue(scope.row.config_data[column]) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </template>

    <template v-else>
      <p class="preview-hint">{{ $t("export.all_preview_hint", { count }) }}</p>
      <el-table :data="previewTables" border stripe max-height="440">
        <el-table-column prop="table_name" :label="$t('overview.table_name')" min-width="220" />
        <el-table-column prop="count" :label="$t('overview.row_count')" width="120" />
        <el-table-column :label="$t('overview.columns')" min-width="360">
          <template #default="scope">{{ (scope.row.columns || []).join(", ") }}</template>
        </el-table-column>
      </el-table>
    </template>

    <template #footer>
      <el-button :disabled="loading" @click="close">{{ $t("dialog.cancel") }}</el-button>
      <el-button type="primary" :loading="loading" @click="$emit('confirm')">
        {{ $t("export.confirm") }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script>
export default {
  name: "ExportPreviewDialog",
  props: {
    visible: { type: Boolean, default: false },
    loading: { type: Boolean, default: false },
    format: { type: String, default: "" },
    scope: { type: String, default: "selected" },
    count: { type: Number, default: 0 },
    rows: { type: Array, default: () => [] },
    columns: { type: Array, default: () => [] },
    tables: { type: Array, default: () => [] },
  },
  data: () => ({ previewLimit: 100 }),
  computed: {
    previewRows() {
      return this.rows.slice(0, this.previewLimit);
    },
    previewTables() {
      return this.tables.slice(0, this.previewLimit);
    },
    hiddenRowCount() {
      return Math.max(0, this.rows.length - this.previewLimit);
    },
  },
  methods: {
    close() {
      if (!this.loading) this.$emit("update:visible", false);
    },
    displayValue(value) {
      if (value === null) return "null";
      if (value === undefined) return "-";
      return typeof value === "string" ? value : JSON.stringify(value);
    },
  },
};
</script>

<style scoped>
.export-summary {
  margin-bottom: 16px;
}
.preview-hint {
  margin: 0 0 12px;
  color: var(--text-secondary);
  font-size: 13px;
}
.cell-value {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 12.5px;
}
</style>
