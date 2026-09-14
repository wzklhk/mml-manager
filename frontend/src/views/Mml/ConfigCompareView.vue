<template>
  <main class="config-compare-page mml-ui">
    <div class="page-content">
      <section class="page-heading">
        <h1>{{ $t("compare.title") }}</h1>
        <p>{{ $t("compare.desc") }}</p>
      </section>

      <el-card v-loading="loadingSnapshots" shadow="never" class="selector-card">
        <el-empty v-if="!loadingSnapshots && snapshots.length < 2" :description="$t('compare.not_enough_configs')" />
        <template v-else>
          <div class="selector-grid">
            <label class="selector-field">
              <span>{{ $t("compare.baseline") }}</span>
              <el-select
                v-model="baselineId"
                filterable
                clearable
                :fit-input-width="true"
                :placeholder="$t('compare.select_placeholder')"
                @change="clearResult"
              >
                <el-option
                  v-for="item in snapshots"
                  :key="item.id"
                  :label="snapshotLabel(item)"
                  :value="item.id"
                  :disabled="item.id === targetId"
                >
                  <span class="snapshot-option-label" :title="snapshotLabel(item)">{{ snapshotLabel(item) }}</span>
                </el-option>
              </el-select>
            </label>
            <label class="selector-field">
              <span>{{ $t("compare.target") }}</span>
              <el-select
                v-model="targetId"
                filterable
                clearable
                :fit-input-width="true"
                :placeholder="$t('compare.select_placeholder')"
                @change="clearResult"
              >
                <el-option
                  v-for="item in snapshots"
                  :key="item.id"
                  :label="snapshotLabel(item)"
                  :value="item.id"
                  :disabled="item.id === baselineId"
                >
                  <span class="snapshot-option-label" :title="snapshotLabel(item)">{{ snapshotLabel(item) }}</span>
                </el-option>
              </el-select>
            </label>
            <el-button type="primary" :loading="comparing" :disabled="!canCompare" @click="compare">
              {{ $t("compare.run") }}
            </el-button>
          </div>
        </template>
      </el-card>

      <el-card v-if="result" shadow="never" class="result-card">
        <div class="summary-grid">
          <div v-for="status in statuses" :key="status" :class="['summary-item', status]">
            <strong>{{ result.summary[status] }}</strong>
            <span>{{ $t("compare." + status) }}</span>
          </div>
        </div>
        <el-collapse v-model="activeTables" class="compare-collapse">
          <el-collapse-item v-for="table in changedTables" :key="table.table_name" :name="table.table_name">
            <template #title>
              <strong>{{ table.table_name }}</strong>
              <el-tag type="success" size="small">+{{ table.summary.added }}</el-tag>
              <el-tag type="danger" size="small">-{{ table.summary.removed }}</el-tag>
              <el-tag type="warning" size="small">~{{ table.summary.modified }}</el-tag>
            </template>
            <el-alert v-if="table.warning" :title="table.warning" type="warning" :closable="false" show-icon />
            <div v-else class="key-hint">{{ $t("compare.key_field") }}: {{ table.key_fields.join(", ") }}</div>
            <div class="diff-table">
              <el-table :data="table.diffs" border stripe max-height="420">
                <el-table-column :label="$t('compare.status')" width="90">
                  <template #default="scope">
                    <el-tag :type="tagType(scope.row.status)" size="small">
                      {{ $t("compare." + scope.row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column
                  prop="key"
                  :label="$t('compare.record')"
                  min-width="180"
                  class-name="compare-value-column"
                />
                <el-table-column :label="$t('compare.details')" min-width="420" class-name="compare-value-column">
                  <template #default="scope">
                    <div v-if="scope.row.changes.length" class="change-list">
                      <div v-for="change in scope.row.changes" :key="change.field">
                        <code>{{ change.field }}</code
                        >: <del>{{ display(change.before) }}</del> →
                        <ins>{{ display(change.after) }}</ins>
                      </div>
                    </div>
                    <pre v-else>{{ JSON.stringify(scope.row.after || scope.row.before, null, 2) }}</pre>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-collapse-item>
        </el-collapse>
        <el-empty v-if="changedTables.length === 0" :description="$t('compare.no_changes')" />
      </el-card>
    </div>
  </main>
</template>

<script>
import apiClient from "../../api/client";

export default {
  name: "ConfigCompareView",
  data: () => ({
    snapshots: [],
    baselineId: "",
    targetId: "",
    loadingSnapshots: false,
    comparing: false,
    result: null,
    activeTables: [],
    statuses: ["added", "removed", "modified", "unchanged"],
  }),
  computed: {
    canCompare() {
      return this.baselineId && this.targetId && this.baselineId !== this.targetId;
    },
    changedTables() {
      return this.result ? this.result.tables.filter((table) => table.diffs.length > 0) : [];
    },
  },
  mounted() {
    this.loadSnapshots();
  },
  methods: {
    async loadSnapshots() {
      this.loadingSnapshots = true;
      try {
        const response = await apiClient.get("/api/snapshots");
        this.snapshots = response.data.snapshots || [];
      } catch (error) {
        this.$message.error(error.response?.data?.error || this.$t("compare.load_failed"));
      } finally {
        this.loadingSnapshots = false;
      }
    },
    snapshotLabel(item) {
      const importedAt = item.loaded_at ? item.loaded_at.replace("T", " ").slice(0, 19) : "";
      const names = item.name && item.name !== item.network_element ? [item.network_element, item.name] : [item.name];
      return [...names, importedAt].filter(Boolean).join(" · ");
    },
    clearResult() {
      this.result = null;
      this.activeTables = [];
    },
    display(value) {
      return value === null || value === undefined || value === "" ? "∅" : String(value);
    },
    tagType(status) {
      return { added: "success", removed: "danger", modified: "warning" }[status] || "info";
    },
    async compare() {
      if (!this.canCompare) return;
      this.comparing = true;
      try {
        const response = await apiClient.post("/api/compare-configurations", {
          baseline_id: this.baselineId,
          target_id: this.targetId,
        });
        this.result = response.data;
        this.activeTables = this.changedTables.slice(0, 1).map((table) => table.table_name);
      } catch (error) {
        this.$message.error(error.response?.data?.error || this.$t("compare.failed"));
      } finally {
        this.comparing = false;
      }
    },
  },
};
</script>

<style scoped>
.config-compare-page {
  flex: 1;
  min-width: 0;
  min-height: 0;
  padding: 28px;
  overflow-x: hidden;
  overflow-y: auto;
  background: var(--bg-secondary);
}
.page-content {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}
.page-heading h1 {
  margin: 0;
  color: var(--text-primary);
  font-size: 26px;
}
.page-heading p {
  margin: 8px 0 20px;
  color: var(--text-muted);
}
.selector-card,
.result-card {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  border-color: var(--border-color);
  background: var(--bg-card);
}
.selector-card :deep(.el-card__body),
.result-card :deep(.el-card__body) {
  padding: 16px;
}
.selector-grid {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(220px, 1fr) auto;
  align-items: end;
  gap: 16px;
}
.selector-field {
  display: grid;
  gap: 8px;
  min-width: 0;
  color: var(--text-primary);
  font-weight: 600;
}
.selector-field .el-select {
  width: 100%;
}
.snapshot-option-label {
  display: block;
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.result-card {
  margin-top: 20px;
}
.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 18px;
}
.summary-item {
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-tertiary);
  text-align: center;
}
.summary-item strong,
.summary-item span {
  display: block;
}
.summary-item strong {
  font-size: 24px;
}
.summary-item span {
  font-size: 12px;
  color: var(--text-muted);
}
.added strong {
  color: #67c23a;
}
.removed strong {
  color: #f56c6c;
}
.modified strong {
  color: #e6a23c;
}
.unchanged strong {
  color: #909399;
}
.compare-collapse {
  display: grid;
  gap: 12px;
  border: 0;
}
.compare-collapse :deep(.el-collapse-item) {
  overflow: hidden;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-card);
}
.compare-collapse :deep(.el-collapse-item__header) {
  min-height: 56px;
  height: auto;
  padding: 10px 16px;
  border-bottom: 0;
  background: var(--bg-card);
}
.compare-collapse :deep(.el-collapse-item.is-active .el-collapse-item__header) {
  border-bottom: 1px solid var(--border-color);
}
.compare-collapse :deep(.el-collapse-item__wrap) {
  border-bottom: 0;
  background: var(--bg-card);
}
.compare-collapse :deep(.el-collapse-item__content) {
  padding: 16px;
}
.compare-collapse .el-tag {
  margin-left: 8px;
}
.key-hint {
  margin: 0 0 10px;
  color: var(--text-muted);
  font-size: 12px;
}
.diff-table {
  overflow: hidden;
  border-radius: 8px;
}
.compare-collapse .el-alert {
  margin-bottom: 12px;
  border-radius: 8px;
}
.change-list {
  line-height: 1.8;
}
.diff-table :deep(td.compare-value-column .cell) {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 12.5px;
  line-height: 1.65;
  color: var(--text-primary);
}
.diff-table code,
.diff-table pre {
  font: inherit;
  color: inherit;
}
.change-list del {
  color: #f56c6c;
}
.change-list ins {
  color: #67c23a;
  text-decoration: none;
}
pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}
@media (max-width: 800px) {
  .config-compare-page {
    padding: 16px;
  }
  .selector-grid {
    grid-template-columns: 1fr;
    align-items: stretch;
  }
  .summary-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
