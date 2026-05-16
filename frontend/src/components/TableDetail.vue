<template>
  <div class="page-content">
    <div class="page-header">
      <h2 class="page-title">
        <i class="el-icon-s-data" style="color: #41b883; margin-right: 8px;"></i>
        {{ tableName }}
      </h2>
      <p class="page-desc">
        {{ columns.length }} 列 ·
        <template v-for="(col, idx) in columns">
          <code class="inline-code" :key="col">{{ col }}<span v-if="idx < columns.length - 1">, </span></code>
        </template>
      </p>
    </div>

    <el-card shadow="never" class="batch-toolbar">
      <el-row type="flex" align="middle">
        <el-col :span="12">
          <span v-if="selectedRows.length > 0" class="batch-info">
            已选择 <strong>{{ selectedRows.length }}</strong> 行
          </span>
          <span v-else class="batch-info" style="color: #999;">
            <i class="el-icon-info"></i> 勾选左侧复选框进行批处理操作
          </span>
        </el-col>
        <el-col :span="12" style="text-align: right;">
          <el-button size="small" type="danger" :disabled="selectedRows.length === 0" @click="$emit('batch-delete')">
            <i class="el-icon-delete"></i> 批量删除
          </el-button>
          <el-button size="small" type="primary" @click="$emit('add-row')">
            <i class="el-icon-plus"></i> 批量添加
          </el-button>
          <el-button size="small" class="vue-btn-outline-green" :disabled="selectedRows.length === 0" @click="$emit('batch-export')">
            <i class="el-icon-download"></i> 批量导出
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never" class="data-card">
      <el-table
        :data="configs"
        style="width: 100%"
        v-loading="loading"
        border stripe max-height="560"
        @sort-change="onSort"
        @selection-change="$emit('selection-change', $event)"
      >
        <el-table-column type="selection" width="45" fixed="left" />
        <el-table-column type="index" label="#" width="50" fixed="left" />
        <el-table-column
          v-for="col in columns" :key="col"
          :prop="'config_data.' + col" :label="col"
          sortable="custom" min-width="130"
        >
          <template slot-scope="scope">
            <span class="cell-value">{{ scope.row.config_data[col] || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template slot-scope="scope">
            <el-button size="mini" type="warning" plain @click="$emit('edit-row', scope.row)">编辑</el-button>
            <el-button size="mini" type="danger" plain @click="$emit('delete-row', scope.row)">删除</el-button>
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
  name: 'TableDetail',
  props: {
    tableName: { type: String, default: '' },
    columns: { type: Array, default: () => [] },
    configs: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false },
    selectedRows: { type: Array, default: () => [] },
    pagination: { type: Object, default: () => ({ page: 1, pageSize: 20, total: 0 }) }
  },
  methods: {
    onSort({ prop, order }) {
      this.$emit('sort-change', { prop, order })
    }
  }
}
</script>

<style scoped>
.page-content { max-width: 1200px; margin: 0 auto; }
.page-header { margin-bottom: 24px; }
.page-title {
  font-size: 24px; font-weight: 600; color: #1a1a2e;
  margin: 0 0 6px 0; display: flex; align-items: center;
}
.page-desc { font-size: 14px; color: #888; margin: 0; line-height: 1.5; }
.inline-code {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  background: #f0f0f0; padding: 1px 6px; border-radius: 4px;
  font-size: 12.5px; color: #476582;
}
.batch-toolbar {
  margin-bottom: 12px; border: 1px solid #e8e8e8;
  border-radius: 8px; background: #fafbfc;
}
.batch-toolbar .el-card__body { padding: 12px 16px; }
.batch-info { font-size: 13px; color: #555; }
.batch-info strong { color: #e6a23c; font-size: 15px; }
.vue-btn-outline-green {
  background: transparent !important;
  border: 1px solid #41b883 !important;
  color: #41b883 !important;
}
.vue-btn-outline-green:hover {
  background: rgba(65,184,131,0.08) !important;
  color: #2c9c6f !important; border-color: #2c9c6f !important;
}
.vue-btn-outline-green.is-disabled { border-color: #ddd !important; color: #ccc !important; }
.data-card { border: 1px solid #e8e8e8; border-radius: 8px; }
.data-card .el-card__body { padding: 16px; }
.cell-value {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 12.5px; color: #333;
}
.pagination-wrapper { margin-top: 20px; display: flex; justify-content: flex-end; }
</style>
