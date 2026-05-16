<template>
  <div id="app" style="display: flex; flex-direction: column; height: 100vh;">
    <VueHeader
      :menu-active="menuActive"
      :selected-table="selectedTable"
      @menu-select="handleMenuSelect"
      @upload-success="handleUploadSuccess"
      @upload-error="handleUploadError"
    />

    <el-container style="flex: 1; overflow: hidden;">
      <Sidebar
        :selected-table="selectedTable"
        :columns="currentColumns"
        :total-rows="pagination.total"
        @back-to-overview="backToOverview"
      />

      <el-main class="vue-main">
        <TableOverview
          v-if="!selectedTable"
          v-model="tableSearch"
          :tables="filteredTables"
          @enter-table="enterTable"
          @refresh="loadTables"
          @sort="handleOverviewSort"
        />

        <TableDetail
          v-if="selectedTable"
          :table-name="selectedTable"
          :columns="currentColumns"
          :configs="configs"
          :loading="loading"
          :selected-rows="selectedRows"
          :pagination="pagination"
          @sort-change="handleSortChange"
          @selection-change="handleSelectionChange"
          @page-change="handlePageChange"
          @size-change="handleSizeChange"
          @batch-delete="batchDelete"
          @batch-export="batchExport"
          @add-row="showAddRowDialog"
          @edit-row="handleEdit"
          @delete-row="handleDelete"
        />

        <div ref="footerSentinel" class="footer-sentinel"></div>
      </el-main>
    </el-container>

    <EditDialog
      :visible.sync="editDialogVisible"
      :is-new-row="isNewRow"
      :columns="currentColumns"
      :form="editForm"
      @save="saveEdit"
    />

    <AppFooter :show-footer="showFooter" />
  </div>
</template>

<script>
import VueHeader from './components/VueHeader.vue'
import Sidebar from './components/Sidebar.vue'
import TableOverview from './components/TableOverview.vue'
import TableDetail from './components/TableDetail.vue'
import EditDialog from './components/EditDialog.vue'
import AppFooter from './components/AppFooter.vue'
import axios from 'axios'

export default {
  name: 'App',
  components: { VueHeader, Sidebar, TableOverview, TableDetail, EditDialog, AppFooter },
  data() {
    return {
      configs: [],
      tables: [],
      selectedTable: '',
      currentColumns: [],
      loading: false,
      tableSearch: '',
      selectedRows: [],
      showFooter: false,
      footerObserver: null,
      pagination: { page: 1, pageSize: 20, total: 0 },
      editDialogVisible: false,
      isNewRow: false,
      editForm: {},
      sort: { prop: null, order: null }
    }
  },
  computed: {
    menuActive() {
      return this.selectedTable ? 'detail' : 'overview'
    },
    filteredTables() {
      if (!this.tableSearch) return this.tables
      const q = this.tableSearch.toLowerCase()
      return this.tables.filter(t => t.table_name.toLowerCase().includes(q))
    }
  },
  mounted() {
    this.loadTables()
    this.$nextTick(() => this.setupFooterObserver())
  },
  beforeDestroy() {
    if (this.footerObserver) this.footerObserver.disconnect()
  },
  methods: {
    setupFooterObserver() {
      const sentinel = this.$refs.footerSentinel
      if (!sentinel) return
      this.footerObserver = new IntersectionObserver(
        (entries) => { this.showFooter = entries[0].isIntersecting },
        { root: null, threshold: 0 }
      )
      this.footerObserver.observe(sentinel)
    },

    handleMenuSelect(index) {
      if (index === 'overview') this.backToOverview()
    },
    handleOverviewSort({ prop, order }) {
      if (!prop || !order) return
      const dir = order === 'ascending' ? 'asc' : 'desc'
      this.tables.sort((a, b) => {
        let va = a[prop], vb = b[prop]
        if (typeof va === 'string') va = va.toLowerCase()
        if (typeof vb === 'string') vb = vb.toLowerCase()
        if (va < vb) return dir === 'asc' ? -1 : 1
        if (va > vb) return dir === 'asc' ? 1 : -1
        return 0
      })
    },

    handleSelectionChange(rows) { this.selectedRows = rows },

    async loadTables() {
      try {
        const res = await axios.get('/api/tables')
        this.tables = res.data.tables
      } catch (e) {
        this.$message.error('加载表名失败: ' + e.message)
      }
    },

    enterTable(row) {
      this.selectedTable = row.table_name
      this.currentColumns = row.columns || []
      this.pagination.page = 1
      this.sort = { prop: null, order: null }
      this.selectedRows = []
      this.loadConfigs()
    },

    backToOverview() {
      this.selectedTable = ''
      this.currentColumns = []
      this.configs = []
      this.selectedRows = []
    },

    handleSortChange({ prop, order }) {
      this.sort.prop = prop ? prop.replace('config_data.', '') : null
      this.sort.order = order === 'ascending' ? 'asc' : order === 'descending' ? 'desc' : null
      this.pagination.page = 1
      this.loadConfigs()
    },

    async loadConfigs() {
      if (!this.selectedTable) return
      this.loading = true
      try {
        const params = {
          page: this.pagination.page,
          page_size: this.pagination.pageSize,
          table_name: this.selectedTable
        }
        if (this.sort.prop) {
          params.sort_by = this.sort.prop
          params.sort_order = this.sort.order
        }
        const res = await axios.get('/api/configs', { params })
        this.configs = res.data.configs
        this.pagination.total = res.data.total
        this.pagination.page = res.data.page
        if (this.configs.length > 0) {
          const keys = Object.keys(this.configs[0].config_data)
          if (keys.length !== this.currentColumns.length) {
            this.currentColumns = keys
          }
        }
      } catch (e) {
        this.$message.error('加载配置失败: ' + e.message)
      } finally {
        this.loading = false
      }
    },

    handleUploadSuccess(response) {
      this.$message.success(response.message)
      this.loadTables()
      if (this.selectedTable) this.loadConfigs()
    },
    handleUploadError(error) {
      this.$message.error('上传失败: ' + error)
    },

    handleSizeChange(size) {
      this.pagination.pageSize = size
      this.pagination.page = 1
      this.loadConfigs()
    },
    handlePageChange(page) {
      this.pagination.page = page
      this.loadConfigs()
    },

    async batchDelete() {
      if (!this.selectedRows.length) return
      this.$confirm(
        `确定要删除选中的 ${this.selectedRows.length} 条配置吗? 删除后不可恢复。`,
        '批量删除',
        { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
      ).then(async () => {
        try {
          const ids = this.selectedRows.map(r => r.id)
          await axios.post('/api/configs/batch-delete', { table_name: this.selectedTable, ids })
          this.$message.success(`成功删除 ${ids.length} 条配置`)
          this.selectedRows = []
          this.loadConfigs()
          this.loadTables()
        } catch (e) {
          this.$message.error('批量删除失败: ' + (e.response?.data?.error || e.message))
        }
      }).catch(() => {})
    },

    async batchExport() {
      if (!this.selectedRows.length) return
      try {
        const ids = this.selectedRows.map(r => r.id)
        const res = await axios.post('/api/export-mml', { table_name: this.selectedTable, ids })
        const blob = new Blob([res.data.content], { type: 'text/plain' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = res.data.filename
        a.click()
        window.URL.revokeObjectURL(url)
        this.$message.success(`成功导出 ${ids.length} 条配置`)
      } catch (e) {
        this.$message.error('导出失败: ' + (e.response?.data?.error || e.message))
      }
    },

    showAddRowDialog() {
      this.isNewRow = true
      this.editForm = {}
      this.currentColumns.forEach(col => { this.editForm[col] = '' })
      this.editDialogVisible = true
    },

    handleEdit(row) {
      this.isNewRow = false
      this.editForm = { ...row.config_data, _id: row.id }
      this.editDialogVisible = true
    },

    async saveEdit() {
      try {
        const configData = {}
        this.currentColumns.forEach(col => { configData[col] = this.editForm[col] || '' })
        if (this.isNewRow) {
          await axios.post('/api/configs', { table_name: this.selectedTable, config_data: configData })
          this.$message.success('新增成功')
        } else {
          await axios.put(`/api/configs/${this.editForm._id}`, { table_name: this.selectedTable, config_data: configData })
          this.$message.success('保存成功')
        }
        this.editDialogVisible = false
        this.loadConfigs()
        this.loadTables()
      } catch (e) {
        this.$message.error('保存失败: ' + e.message)
      }
    },

    handleDelete(row) {
      this.$confirm('确定要删除这条配置吗? 删除后不可恢复。', '确认删除', {
        confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning'
      }).then(async () => {
        try {
          await axios.delete(`/api/configs/${row.id}`, { params: { table_name: this.selectedTable } })
          this.$message.success('删除成功')
          this.loadConfigs()
        } catch (e) {
          this.$message.error('删除失败: ' + e.message)
        }
      }).catch(() => {})
    }
  }
}
</script>

<style>
/* ====== 全局样式（unscoped） ====== */
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body {
  height: 100%; margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f5f7fa; color: #213547;
  -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
}
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
}

/* 通用内容区 */
.vue-main { background: #f5f7fa; padding: 24px 32px; overflow-y: auto; }
.footer-sentinel { height: 1px; }

/* ====== Element UI 主题微调 ====== */
.el-table { border-radius: 6px; }
.el-table th.el-table__cell {
  background: #f8f9fc !important; color: #555; font-weight: 600; font-size: 13px;
}
.el-table .cell { line-height: 1.5; }
.el-button--success { background: #41b883; border-color: #41b883; }
.el-button--success:hover { background: #3aa876; border-color: #3aa876; }
.el-button--primary { background: #3eaf7c; border-color: #3eaf7c; }
.el-button--primary:hover { background: #349b6b; border-color: #349b6b; }
.el-button--primary.is-plain { color: #3eaf7c; background: #f0f9f4; border-color: #b8e6d0; }
.el-button--primary.is-plain:hover { color: #2c9c6f; background: #d0f0e0; border-color: #8dd4b4; }
.el-button--warning.is-plain { color: #e6a23c; background: #fdf6ec; border-color: #f5dab1; }
.el-pagination.is-background .el-pager li:not(.disabled).active { background: #41b883; }
.el-pagination.is-background .el-pager li:not(.disabled):hover { color: #41b883; }
.el-tag--success.el-tag--dark { background: #41b883; border-color: #41b883; }
.el-link.el-link--primary { color: #3eaf7c; }
.el-input__inner:focus { border-color: #41b883; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #aaa; }
</style>
