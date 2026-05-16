<template>
  <div class="page-content">
    <div class="page-header">
      <h2 class="page-title">表概览</h2>
      <p class="page-desc">数据库中的所有配置表</p>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-row :gutter="16" type="flex" align="middle">
        <el-col :span="8">
          <el-input
            :value="value"
            @input="$emit('input', $event)"
            placeholder="搜索表名..."
            prefix-icon="el-icon-search"
            clearable
            size="medium"
          />
        </el-col>
        <el-col :span="16" style="text-align: right;">
          <el-button icon="el-icon-refresh" size="small" @click="$emit('refresh')">刷新</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never" class="data-card">
      <el-table :data="tables" style="width: 100%" border stripe @sort-change="onSort">
        <el-table-column label="表名" min-width="220" sortable="custom" prop="table_name">
          <template slot-scope="scope">
            <el-link type="primary" :underline="false" @click="$emit('enter-table', scope.row)" class="table-link">
              <i class="el-icon-s-data" style="margin-right: 4px;"></i>
              {{ scope.row.table_name }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column label="列" min-width="320">
          <template slot-scope="scope">
            <el-tag v-for="col in scope.row.columns" :key="col" size="mini" class="col-tag">{{ col }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="count" label="行数" width="100" sortable="custom" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="180" sortable="custom" />
        <el-table-column label="操作" width="100" align="center">
          <template slot-scope="scope">
            <el-button size="mini" type="primary" plain @click="$emit('enter-table', scope.row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'TableOverview',
  props: {
    tables: { type: Array, default: () => [] },
    value: { type: String, default: '' }
  },
  methods: {
    onSort({ prop, order }) {
      if (!prop || !order) return
      this.$emit('sort', { prop, order })
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
.filter-card {
  margin-bottom: 16px; border: 1px solid #e8e8e8; border-radius: 8px;
}
.data-card { border: 1px solid #e8e8e8; border-radius: 8px; }
.data-card .el-card__body { padding: 16px; }
.table-link { font-weight: 500; }
.table-link:hover { color: #2c9c6f !important; }
.col-tag {
  margin: 2px 3px; border: none; background: #e8f5e9; color: #2e7d32;
}
</style>
