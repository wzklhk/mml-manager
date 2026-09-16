<template>
  <div class="page-content">
    <div class="page-header">
      <div class="page-title-row">
        <h2 class="page-title">
          <i class="el-icon-s-data" style="color: #41b883; margin-right: 8px"></i>
          {{ tableName }}
        </h2>
        <el-button plain @click="$emit('edit-table')">{{ $t("detail.edit_fields") }}</el-button>
      </div>
      <p class="page-desc">
        {{ columns.length }} {{ $t("detail.columns") }} &middot;
        <template v-for="(col, idx) in columns" :key="col">
          <code class="inline-code">
            {{ col }} ({{ typeLabel(columnTypes[col]) }})<span v-if="idx < columns.length - 1">, </span>
          </code>
        </template>
      </p>
    </div>

    <el-card shadow="never" class="batch-toolbar">
      <div class="mml-toolbar">
        <span class="batch-info">
          {{
            selectedRows.length ? $t("detail.selected_rows", { count: selectedRows.length }) : $t("detail.batch_hint")
          }}
        </span>
        <div class="mml-actions">
          <el-button type="primary" @click="$emit('add-row')">{{ $t("detail.add_config") }}</el-button>
          <el-dropdown :disabled="selectedRows.length === 0" @command="$emit('batch-export', $event)">
            <el-button :disabled="selectedRows.length === 0">
              {{ $t("detail.batch_export") }}
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="mml">MML</el-dropdown-item>
                <el-dropdown-item command="csv">CSV</el-dropdown-item>
                <el-dropdown-item command="xlsx">Excel (.xlsx)</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button type="danger" plain :disabled="selectedRows.length === 0" @click="$emit('batch-delete')">{{
            $t("detail.batch_delete")
          }}</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="data-card">
      <el-table
        ref="configTable"
        :data="configs"
        row-key="id"
        style="width: 100%"
        v-loading="loading"
        border
        stripe
        @sort-change="onSort"
        @selection-change="$emit('selection-change', $event)"
      >
        <el-table-column type="selection" width="45" fixed="left" reserve-selection />
        <el-table-column type="index" label="#" width="50" fixed="left" />
        <el-table-column
          v-for="col in displayedColumns"
          :key="col"
          :prop="'config_data.' + col"
          :label="col"
          sortable="custom"
          min-width="130"
          :fixed="isPinned(col) ? 'left' : false"
        >
          <template #header>
            <div class="column-header">
              <div class="column-title-row">
                <span class="column-title" :title="col">{{ col }}</span>
                <el-tooltip
                  :content="isPinned(col) ? $t('detail.unpin_column') : $t('detail.pin_column')"
                  placement="top"
                >
                  <button
                    type="button"
                    class="pin-button"
                    :class="{ active: isPinned(col) }"
                    :aria-label="isPinned(col) ? $t('detail.unpin_column') : $t('detail.pin_column')"
                    @click.stop="togglePinnedColumn(col)"
                  >
                    <span aria-hidden="true">📌</span>
                  </button>
                </el-tooltip>
              </div>
              <el-input
                v-model="columnFilters[col]"
                size="small"
                clearable
                :placeholder="$t('detail.filter_placeholder')"
                @input="scheduleFilterChange"
                @clear="emitFilterChange"
                @click.stop
              />
            </div>
          </template>
          <template #default="scope">
            <span class="cell-value">{{ scope.row.config_data[col] ?? "-" }}</span>
          </template>
        </el-table-column>
        <el-table-column
          :label="$t('detail.actions')"
          :width="actionColumnWidth || undefined"
          fixed="right"
          header-align="left"
          class-name="actions-column"
          label-class-name="actions-column-header"
        >
          <template #header>
            <div class="column-header">
              <div class="column-title-row">
                <span class="column-title actions-column-title">{{ $t("detail.actions") }}</span>
              </div>
              <div class="actions-filter-placeholder" aria-hidden="true"></div>
            </div>
          </template>
          <template #default="scope">
            <div class="mml-row-actions">
              <el-button size="small" @click="$emit('edit-row', scope.row)">{{ $t("detail.edit") }}</el-button>
              <el-button size="small" type="danger" plain @click="$emit('delete-row', scope.row)">{{
                $t("detail.delete")
              }}</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          @current-change="$emit('page-change', $event)"
          @size-change="$emit('size-change', $event)"
          :current-page="pagination.page"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          background
        />
      </div>
    </el-card>
  </div>
</template>

<script>
import { measureActionColumnWidth } from "../utils/actionColumnWidth";

export default {
  name: "TableDetail",
  props: {
    tableName: { type: String, default: "" },
    columns: { type: Array, default: () => [] },
    columnTypes: { type: Object, default: () => ({}) },
    configs: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false },
    selectedRows: { type: Array, default: () => [] },
    pagination: { type: Object, default: () => ({ page: 1, pageSize: 20, total: 0 }) },
  },
  data() {
    return {
      columnFilters: {},
      pinnedColumns: [],
      filterTimer: null,
      actionColumnWidth: null,
      actionResizeFrame: null,
    };
  },
  computed: {
    displayedColumns() {
      const pinned = this.pinnedColumns.filter((column) => this.columns.includes(column));
      return [...pinned, ...this.columns.filter((column) => !pinned.includes(column))];
    },
  },
  watch: {
    tableName() {
      this.resetColumnTools();
    },
    columns: {
      immediate: true,
      handler(columns) {
        const nextFilters = {};
        columns.forEach((column) => {
          nextFilters[column] = this.columnFilters[column] || "";
        });
        this.columnFilters = nextFilters;
        this.pinnedColumns = this.pinnedColumns.filter((column) => columns.includes(column));
      },
    },
  },
  beforeUnmount() {
    window.clearTimeout(this.filterTimer);
    window.cancelAnimationFrame(this.actionResizeFrame);
  },
  mounted() {
    this.queueActionColumnResize();
  },
  updated() {
    this.queueActionColumnResize();
  },
  methods: {
    typeLabel(dataType) {
      return dataType ? this.$t(`overview.type_${dataType}`) : this.$t("overview.type_unknown");
    },
    queueActionColumnResize() {
      if (this.actionResizeFrame) return;
      this.actionResizeFrame = window.requestAnimationFrame(() => {
        this.actionResizeFrame = null;
        const measuredWidth = measureActionColumnWidth(this.$el);
        if (measuredWidth && measuredWidth !== this.actionColumnWidth) {
          this.actionColumnWidth = measuredWidth;
        }
      });
    },
    clearSelection() {
      this.$refs.configTable?.clearSelection();
    },
    onSort({ prop, order }) {
      this.$emit("sort-change", { prop, order });
    },
    scheduleFilterChange() {
      window.clearTimeout(this.filterTimer);
      this.filterTimer = window.setTimeout(this.emitFilterChange, 300);
    },
    emitFilterChange() {
      window.clearTimeout(this.filterTimer);
      const filters = Object.fromEntries(
        Object.entries(this.columnFilters)
          .map(([field, value]) => [field, value.trim()])
          .filter(([, value]) => value),
      );
      this.$emit("filter-change", filters);
    },
    togglePinnedColumn(column) {
      if (this.isPinned(column)) {
        this.pinnedColumns = this.pinnedColumns.filter((item) => item !== column);
      } else {
        this.pinnedColumns = [...this.pinnedColumns, column];
      }
    },
    isPinned(column) {
      return this.pinnedColumns.includes(column);
    },
    resetColumnTools() {
      window.clearTimeout(this.filterTimer);
      this.columnFilters = {};
      this.pinnedColumns = [];
    },
  },
};
</script>

<style scoped>
.page-content {
  width: 100%;
}
.page-header {
  margin-bottom: 24px;
}
.page-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 6px;
}
.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
}
.page-desc {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.5;
}
.inline-code {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  background: var(--inline-code-bg);
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 12.5px;
  color: var(--inline-code-color);
}
.batch-toolbar {
  margin-bottom: 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-tertiary);
}
.batch-toolbar .el-card__body {
  padding: 12px 16px;
}
.batch-info {
  font-size: 13px;
  color: var(--text-secondary);
}
.batch-info strong {
  color: #e6a23c;
  font-size: 15px;
}
.data-card {
  border: 1px solid var(--border-color);
  border-radius: 8px;
}
.data-card .el-card__body {
  padding: 16px;
}
.cell-value {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 12.5px;
  color: var(--text-primary);
}
.column-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 4px 0;
}
.column-title-row {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
}
.column-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.pin-button {
  flex: none;
  width: 24px;
  height: 24px;
  padding: 0;
  border: 0;
  border-radius: 4px;
  color: var(--text-muted);
  background: transparent;
  cursor: pointer;
  filter: grayscale(1);
  opacity: 0.55;
}
.pin-button:hover,
.pin-button.active {
  background: var(--bg-tertiary);
  filter: none;
  opacity: 1;
}
.column-header :deep(.el-input__wrapper) {
  padding: 0 7px;
}
.actions-filter-placeholder {
  height: var(--el-component-size-small);
}
.actions-column-title {
  flex: none;
}
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
:deep(td.actions-column .cell) {
  display: flex;
  justify-content: flex-end;
}
</style>
