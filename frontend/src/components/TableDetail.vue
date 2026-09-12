<template>
  <div class="page-content">
    <div class="page-header">
      <h2 class="page-title">
        <i class="el-icon-s-data" style="color: #41b883; margin-right: 8px"></i>
        {{ tableName }}
      </h2>
      <p class="page-desc">
        {{ columns.length }} {{ $t("detail.columns") }} &middot;
        <template v-for="(col, idx) in columns" :key="col">
          <code class="inline-code">{{ col }}<span v-if="idx < columns.length - 1">, </span></code>
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
          <el-button type="danger" plain :disabled="selectedRows.length === 0" @click="$emit('batch-delete')">{{
            $t("detail.batch_delete")
          }}</el-button>
          <el-dropdown :disabled="selectedRows.length === 0" @command="$emit('batch-export', $event)">
            <el-button :disabled="selectedRows.length === 0">
              {{ $t("detail.batch_export") }}<i class="el-icon-arrow-down el-icon--right"></i>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="mml">MML</el-dropdown-item>
                <el-dropdown-item command="csv">CSV</el-dropdown-item>
                <el-dropdown-item command="xlsx">Excel (.xlsx)</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button type="primary" @click="$emit('add-row')">{{ $t("detail.batch_add") }}</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="data-card">
      <el-table
        :data="configs"
        style="width: 100%"
        v-loading="loading"
        border
        stripe
        max-height="560"
        @sort-change="onSort"
        @selection-change="$emit('selection-change', $event)"
      >
        <el-table-column type="selection" width="45" fixed="left" />
        <el-table-column type="index" label="#" width="50" fixed="left" />
        <el-table-column
          v-for="col in columns"
          :key="col"
          :prop="'config_data.' + col"
          :label="col"
          sortable="custom"
          min-width="130"
        >
          <template #default="scope">
            <span class="cell-value">{{ scope.row.config_data[col] || "-" }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('detail.actions')" width="184" fixed="right" align="right">
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
export default {
  name: "TableDetail",
  props: {
    tableName: { type: String, default: "" },
    columns: { type: Array, default: () => [] },
    configs: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false },
    selectedRows: { type: Array, default: () => [] },
    pagination: { type: Object, default: () => ({ page: 1, pageSize: 20, total: 0 }) },
  },
  methods: {
    onSort({ prop, order }) {
      this.$emit("sort-change", { prop, order });
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
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
