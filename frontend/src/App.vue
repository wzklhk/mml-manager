<template>
  <div id="app" :class="{ dark: isDark }" style="display: flex; flex-direction: column; height: 100vh;">
    <VueHeader
      :menu-active="menuActive"
      :selected-table="selectedTable"
      :is-dark="isDark"
      @menu-select="handleMenuSelect"
      @upload-start="handleUploadStart"
      @upload-success="handleUploadSuccess"
      @upload-error="handleUploadError"
      @toggle-theme="toggleTheme"
      @toggle-lang="toggleLang"
      @logo-click="backToOverview"
    />

    <el-container
      v-loading="uploading"
      element-loading-text=" importing..."
      element-loading-spinner="el-icon-loading"
      style="flex: 1; overflow: hidden;"
    >
      <Sidebar
        :selected-table="selectedTable"
        :tables="tables"
        :columns="currentColumns"
        :total-rows="pagination.total"
        :collapsed="sidebarCollapsed"
        @toggle-sidebar="sidebarCollapsed = !sidebarCollapsed"
        @select-table="enterTable"
      />

      <el-main class="vue-main">
        <TableOverview
          v-show="!selectedTable"
          v-model="tableSearch"
          :tables="filteredTables"
          @enter-table="enterTable"
          @refresh="loadTables"
          @sort="handleOverviewSort"
        />

        <TableDetail
          v-show="selectedTable"
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
      sidebarCollapsed: false,
      pagination: { page: 1, pageSize: 20, total: 0 },
      editDialogVisible: false,
      isNewRow: false,
      editForm: {},
      sort: { prop: null, order: null },
      isDark: localStorage.getItem('theme') === 'dark',
      uploading: false
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
    this.applyTheme()
    this.loadTables()
    document.title = this.$t('app.title')
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

    applyTheme() {
      if (this.isDark) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
    },

    toggleTheme() {
      this.isDark = !this.isDark
      localStorage.setItem('theme', this.isDark ? 'dark' : 'light')
      this.applyTheme()
    },

    toggleLang() {
      const newLocale = this.$i18n.locale === 'zh' ? 'en' : 'zh'
      this.$i18n.locale = newLocale
      localStorage.setItem('locale', newLocale)
      document.title = this.$t('app.title')
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
        this.$message.error(this.$t('msg.load_tables_fail', { msg: e.message }))
      }
    },

    enterTable(row) {
      this.selectedTable = row.table_name
      this.currentColumns = row.columns || []
      this.pagination.page = 1
      this.sort = { prop: null, order: null }
      this.selectedRows = []
      this.sidebarCollapsed = false
      this.loadConfigs()
    },

    backToOverview() {
      this.selectedTable = ''
      this.currentColumns = []
      this.configs = []
      this.selectedRows = []
      this.sidebarCollapsed = false
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
        this.$message.error(this.$t('msg.load_configs_fail', { msg: e.message }))
      } finally {
        this.loading = false
      }
    },

    handleUploadStart() {
      this.uploading = true
    },
    handleUploadSuccess(response) {
      this.uploading = false
      this.$message.success(response.message)
      this.loadTables()
      if (this.selectedTable) this.loadConfigs()
    },
    handleUploadError(error) {
      this.uploading = false
      const msg = error?.message || (typeof error === 'string' ? error : null) || this.$t('msg.upload_fail')
      this.$message.error(msg)
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
      const count = this.selectedRows.length
      this.$confirm(
        this.$t('confirm.batch_delete_content', { count }),
        this.$t('confirm.batch_delete_title'),
        { confirmButtonText: this.$t('confirm.btn_confirm'), cancelButtonText: this.$t('confirm.btn_cancel'), type: 'warning' }
      ).then(async () => {
        try {
          const ids = this.selectedRows.map(r => r.id)
          await axios.post('/api/configs/batch-delete', { table_name: this.selectedTable, ids })
          this.$message.success(this.$t('msg.batch_delete_success', { count: ids.length }))
          this.selectedRows = []
          this.loadConfigs()
          this.loadTables()
        } catch (e) {
          this.$message.error(this.$t('msg.batch_delete_fail', { msg: e.response?.data?.error || e.message }))
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
        this.$message.success(this.$t('msg.export_success', { count: ids.length }))
      } catch (e) {
        this.$message.error(this.$t('msg.export_fail', { msg: e.response?.data?.error || e.message }))
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
          this.$message.success(this.$t('msg.add_success'))
        } else {
          await axios.put(`/api/configs/${this.editForm._id}`, { table_name: this.selectedTable, config_data: configData })
          this.$message.success(this.$t('msg.save_success'))
        }
        this.editDialogVisible = false
        this.loadConfigs()
        this.loadTables()
      } catch (e) {
        this.$message.error(this.$t('msg.save_fail', { msg: e.message }))
      }
    },

    handleDelete(row) {
      this.$confirm(
        this.$t('confirm.delete_content'),
        this.$t('confirm.delete_title'),
        { confirmButtonText: this.$t('confirm.btn_confirm'), cancelButtonText: this.$t('confirm.btn_cancel'), type: 'warning' }
      ).then(async () => {
        try {
          await axios.delete(`/api/configs/${row.id}`, { params: { table_name: this.selectedTable } })
          this.$message.success(this.$t('msg.delete_success'))
          this.loadConfigs()
        } catch (e) {
          this.$message.error(this.$t('msg.delete_fail', { msg: e.message }))
        }
      }).catch(() => {})
    }
  }
}
</script>
