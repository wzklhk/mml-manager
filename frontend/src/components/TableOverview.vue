<template>
  <div class="page-content">
    <div class="page-header">
      <h2 class="page-title">{{ $t("overview.title") }}</h2>
      <p class="page-desc">{{ $t("overview.desc") }}</p>
    </div>

    <el-card shadow="never" class="filter-card">
      <div class="mml-toolbar">
        <div class="mml-search">
          <el-input
            :model-value="modelValue"
            @update:model-value="$emit('update:modelValue', $event)"
            :placeholder="$t('overview.search_placeholder')"
            clearable
            size="default"
          />
        </div>
        <div class="mml-actions">
          <el-button type="primary" :disabled="!canManageTables" @click="$emit('add-table')">
            {{ $t("overview.add_table") }}
          </el-button>
          <el-dropdown :disabled="!canExport" @command="$emit('export-all', $event)">
            <el-button type="primary" :disabled="!canExport">
              {{ $t("export.all") }}
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="mml">MML</el-dropdown-item>
                <el-dropdown-item command="csv">CSV</el-dropdown-item>
                <el-dropdown-item command="xlsx">Excel (.xlsx)</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="data-card">
      <el-table :data="tables" style="width: 100%" border stripe @sort-change="onSort">
        <el-table-column :label="$t('overview.table_name')" min-width="220" sortable="custom" prop="table_name">
          <template #default="scope">
            <el-link type="primary" underline="never" @click="$emit('enter-table', scope.row)" class="table-link">
              <i class="el-icon-s-data" style="margin-right: 4px"></i>
              {{ scope.row.table_name }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column :label="$t('overview.columns')" min-width="320">
          <template #default="scope">
            <el-tag v-for="col in scope.row.columns" :key="col" size="small" class="col-tag">{{ col }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('overview.row_count')" prop="count" width="100" sortable="custom" align="center" />
        <el-table-column :label="$t('overview.created_at')" prop="created_at" width="180" sortable="custom" />
        <el-table-column
          :label="$t('overview.actions')"
          :width="actionColumnWidth || undefined"
          fixed="right"
          header-align="left"
          class-name="actions-column"
          label-class-name="actions-column-header"
        >
          <template #header>
            <span class="actions-column-title">{{ $t("overview.actions") }}</span>
          </template>
          <template #default="scope">
            <div class="mml-row-actions">
              <el-button size="small" @click="$emit('enter-table', scope.row)">{{ $t("overview.view") }}</el-button>
              <el-button size="small" type="danger" plain @click="$emit('delete-table', scope.row)">
                {{ $t("overview.delete") }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrapper">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next"
          :current-page="pagination.page"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          @current-change="$emit('page-change', $event)"
          @size-change="$emit('size-change', $event)"
        />
      </div>
    </el-card>
  </div>
</template>

<script>
import { measureActionColumnWidth } from "../utils/actionColumnWidth";

export default {
  name: "TableOverview",
  props: {
    tables: { type: Array, default: () => [] },
    canExport: { type: Boolean, default: false },
    canManageTables: { type: Boolean, default: false },
    modelValue: { type: String, default: "" },
    pagination: { type: Object, default: () => ({ page: 1, pageSize: 20, total: 0 }) },
  },
  data() {
    return {
      actionColumnWidth: null,
      actionResizeFrame: null,
    };
  },
  mounted() {
    this.queueActionColumnResize();
  },
  updated() {
    this.queueActionColumnResize();
  },
  beforeUnmount() {
    window.cancelAnimationFrame(this.actionResizeFrame);
  },
  methods: {
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
    onSort({ prop, order }) {
      if (!prop || !order) return;
      this.$emit("sort", { prop, order });
    },
  },
};
</script>

<style scoped>
.page-content {
  max-width: 1200px;
  margin: 0 auto;
}
.page-header {
  margin-bottom: 24px;
}
.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px 0;
  display: flex;
  align-items: center;
}
.page-desc {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.5;
}
.filter-card {
  margin-bottom: 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
}
.data-card {
  border: 1px solid var(--border-color);
  border-radius: 8px;
}
.data-card .el-card__body {
  padding: 16px;
}
.table-link {
  font-weight: 500;
}
.table-link:hover {
  color: #2c9c6f !important;
}
.col-tag {
  margin: 2px 3px;
  border: none;
  background: var(--tag-bg);
  color: var(--tag-color);
}
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  overflow-x: auto;
}
:deep(td.actions-column .cell) {
  display: flex;
  justify-content: flex-end;
}
.actions-column-title {
  display: inline-block;
}
</style>
