<template>
  <div id="app" style="display: flex; flex-direction: column; height: 100vh;">
      <!-- ========== 顶部导航栏 ========== -->
      <el-header class="vue-header">
        <div class="header-left">
          <div class="header-logo">
            <svg class="vue-logo" viewBox="0 0 261.76 226.69" width="28" height="24">
              <path d="M161.096.001l-30.224 52.35L100.647.002H-.005l130.877 226.688L261.76.001z" fill="#41b883"/>
              <path d="M161.096.001l-30.224 52.35L100.647.002H52.346l78.526 136.01L209.398.001z" fill="#34495e"/>
            </svg>
            <span class="header-title">MML 配置管理系统</span>
          </div>
          <el-menu
            :default-active="menuActive"
            mode="horizontal"
            class="vue-nav-menu"
            @select="handleMenuSelect"
            background-color="transparent"
            text-color="rgba(255,255,255,0.7)"
            active-text-color="#fff"
          >
            <el-menu-item index="overview">
              <i class="el-icon-menu"></i>
              表概览
            </el-menu-item>
            <el-menu-item v-if="selectedTable" index="detail">
              <i class="el-icon-document"></i>
              {{ selectedTable }}
            </el-menu-item>
          </el-menu>
        </div>
        <div class="header-right">
          <a href="https://github.com/wzklhk/mml-manager" target="_blank" class="github-link" title="GitHub 仓库">
            <svg viewBox="0 0 16 16" width="18" height="18" fill="rgba(255,255,255,0.75)">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
            </svg>
          </a>
          <el-upload
            class="header-upload"
            action="/api/import-mml"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :before-upload="beforeUpload"
            accept=".mml"
            :show-file-list="false"
          >
            <el-button size="small" class="vue-btn-outline">
              <i class="el-icon-upload2"></i> 导入 MML
            </el-button>
          </el-upload>
        </div>
      </el-header>

      <!-- ========== 主体区域（侧边栏 + 内容） ========== -->
      <el-container style="flex: 1; overflow: hidden;">
        <!-- 侧边栏 -->
        <el-aside :width="selectedTable ? '260px' : '0'" class="vue-aside">
          <div v-if="selectedTable" class="aside-content">
            <div class="aside-header">
              <h3 class="aside-title">
                <i class="el-icon-s-grid" style="color: #41b883; margin-right: 6px;"></i>
                {{ selectedTable }}
              </h3>
              <el-tag size="small" type="success" effect="dark">{{ pagination.total }} 行</el-tag>
            </div>

            <!-- 列列表 -->
            <div class="aside-section">
              <div class="aside-section-title">列</div>
              <div class="aside-column-list">
                <div
                  v-for="col in currentColumns"
                  :key="col"
                  class="aside-column-item"
                >
                  <span class="col-dot"></span>
                  <span class="col-name">{{ col }}</span>
                </div>
              </div>
            </div>

            <!-- 导航按钮 -->
            <div class="aside-actions">
              <el-button size="small" icon="el-icon-back" @click="backToOverview" class="aside-back-btn">
                返回概览
              </el-button>
            </div>
          </div>
        </el-aside>

        <!-- 主体内容 -->
        <el-main class="vue-main">
          <!-- ========== 所有表概览 ========== -->
          <div v-if="!selectedTable" class="page-content">
            <div class="page-header">
              <h2 class="page-title">表概览</h2>
              <p class="page-desc">数据库中的所有配置表</p>
            </div>

            <!-- 搜索和操作栏 -->
            <el-card shadow="never" class="filter-card">
              <el-row :gutter="16" type="flex" align="middle">
                <el-col :span="8">
                  <el-input
                    v-model="tableSearch"
                    placeholder="搜索表名..."
                    prefix-icon="el-icon-search"
                    clearable
                    size="medium"
                  />
                </el-col>
                <el-col :span="16" style="text-align: right;">
                  <el-button icon="el-icon-refresh" size="small" @click="loadTables">刷新</el-button>
                </el-col>
              </el-row>
            </el-card>

            <!-- 表格卡片 -->
            <el-card shadow="never" class="data-card">
              <el-table
                :data="filteredTables"
                style="width: 100%"
                border
                stripe
                @sort-change="handleOverviewSort"
              >
                <el-table-column label="表名" min-width="220" sortable="custom" prop="table_name">
                  <template slot-scope="scope">
                    <el-link type="primary" :underline="false" @click="enterTable(scope.row)" class="table-link">
                      <i class="el-icon-s-data" style="margin-right: 4px;"></i>
                      {{ scope.row.table_name }}
                    </el-link>
                  </template>
                </el-table-column>
                <el-table-column label="列" min-width="320">
                  <template slot-scope="scope">
                    <el-tag
                      v-for="col in scope.row.columns"
                      :key="col"
                      size="mini"
                      class="col-tag"
                    >{{ col }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="count" label="行数" width="100" sortable="custom" align="center" />
                <el-table-column prop="created_at" label="创建时间" width="180" sortable="custom" />
                <el-table-column label="操作" width="100" align="center">
                  <template slot-scope="scope">
                    <el-button size="mini" type="primary" plain @click="enterTable(scope.row)">查看</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>

          <!-- ========== 表详情（进入表后） ========== -->
          <div v-if="selectedTable" class="page-content">
            <div class="page-header">
              <h2 class="page-title">
                <i class="el-icon-s-data" style="color: #41b883; margin-right: 8px;"></i>
                {{ selectedTable }}
              </h2>
              <p class="page-desc">
                {{ currentColumns.length }} 列 ·
                <template v-for="(col, idx) in currentColumns">
                  <code class="inline-code" :key="col">{{ col }}<span v-if="idx < currentColumns.length - 1">, </span></code>
                </template>
              </p>
            </div>

            <!-- ===== 批处理工具栏 ===== -->
            <el-card shadow="never" class="batch-toolbar">
              <el-row type="flex" align="middle">
                <el-col :span="12">
                  <span class="batch-info" v-if="selectedRows.length > 0">
                    已选择 <strong>{{ selectedRows.length }}</strong> 行
                  </span>
                  <span class="batch-info" v-else style="color: #999;">
                    <i class="el-icon-info"></i> 勾选左侧复选框进行批处理操作
                  </span>
                </el-col>
                <el-col :span="12" style="text-align: right;">
                  <el-button
                    size="small"
                    type="danger"
                    :disabled="selectedRows.length === 0"
                    @click="batchDelete"
                  >
                    <i class="el-icon-delete"></i> 批量删除
                  </el-button>
                  <el-button
                    size="small"
                    type="primary"
                    @click="showAddRowDialog"
                  >
                    <i class="el-icon-plus"></i> 批量添加
                  </el-button>
                  <el-button
                    size="small"
                    class="vue-btn-outline-green"
                    :disabled="selectedRows.length === 0"
                    @click="batchExport"
                  >
                    <i class="el-icon-download"></i> 批量导出
                  </el-button>
                </el-col>
              </el-row>
            </el-card>

            <!-- 数据表 -->
            <el-card shadow="never" class="data-card">
              <el-table
                ref="dataTable"
                :data="configs"
                style="width: 100%"
                v-loading="loading"
                border
                stripe
                max-height="560"
                @sort-change="handleSortChange"
                @selection-change="handleSelectionChange"
              >
                <el-table-column type="selection" width="45" fixed="left" />
                <el-table-column type="index" label="#" width="50" fixed="left" />
                <!-- 动态列 -->
                <el-table-column
                  v-for="col in currentColumns"
                  :key="col"
                  :prop="'config_data.' + col"
                  :label="col"
                  sortable="custom"
                  min-width="130"
                >
                  <template slot-scope="scope">
                    <span class="cell-value">{{ scope.row.config_data[col] || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="150" fixed="right">
                  <template slot-scope="scope">
                    <el-button size="mini" type="warning" plain @click="handleEdit(scope.row)">编辑</el-button>
                    <el-button size="mini" type="danger" plain @click="handleDelete(scope.row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>

              <!-- 分页 -->
              <div class="pagination-wrapper">
                <el-pagination
                  @current-change="handlePageChange"
                  @size-change="handleSizeChange"
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

          <!-- 底部哨兵：用于触发 footer 显示 -->
          <div ref="footerSentinel" class="footer-sentinel"></div>
        </el-main>
      </el-container>

    <!-- 编辑/新增对话框 -->
    <el-dialog
      :title="isNewRow ? '新增行' : '编辑配置'"
      :visible.sync="editDialogVisible"
      width="520px"
      :close-on-click-modal="false"
      top="8vh"
    >
      <el-form :model="editForm" label-width="110px" size="small">
        <el-form-item
          v-for="col in currentColumns"
          :key="col"
          :label="col"
        >
          <el-input v-model="editForm[col]" :placeholder="'请输入 ' + col" clearable />
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="success" @click="saveEdit">{{ isNewRow ? '新增' : '保存' }}</el-button>
      </span>
    </el-dialog>

    <!-- ========== 底部（License + Copyright，滚动到底才显示） ========== -->
    <footer v-show="showFooter" class="vue-footer">
      <div class="footer-content">
        <span class="footer-license">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="#999" style="vertical-align: -2px; margin-right: 4px;">
            <path d="M12 2L2 7v5c0 5.25 3.86 10.14 10 11 6.14-.86 10-5.75 10-11V7l-10-5z"/>
          </svg>
          MIT License
        </span>
        <span class="footer-sep">·</span>
        <span class="footer-copyright">
          &copy; {{ new Date().getFullYear() }} Kaihao Wei. All rights reserved.
        </span>
      </div>
    </footer>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
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
      pagination: {
        page: 1,
        pageSize: 20,
        total: 0
      },
      editDialogVisible: false,
      isNewRow: false,
      editForm: {},
      sort: {
        prop: null,
        order: null
      }
    }
  },
  computed: {
    menuActive() {
      if (this.selectedTable) return 'detail'
      return 'overview'
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
    if (this.footerObserver) {
      this.footerObserver.disconnect()
    }
  },
  methods: {
    setupFooterObserver() {
      const sentinel = this.$refs.footerSentinel
      if (!sentinel) return
      this.footerObserver = new IntersectionObserver(
        (entries) => {
          this.showFooter = entries[0].isIntersecting
        },
        { root: null, threshold: 0 }
      )
      this.footerObserver.observe(sentinel)
    },

    handleMenuSelect(index) {
      if (index === 'overview') {
        this.backToOverview()
      }
    },

    handleOverviewSort({ prop, order }) {
      if (!prop || !order) return
      const dir = order === 'ascending' ? 'asc' : 'desc'
      this.tables.sort((a, b) => {
        let va = a[prop]
        let vb = b[prop]
        if (typeof va === 'string') va = va.toLowerCase()
        if (typeof vb === 'string') vb = vb.toLowerCase()
        if (va < vb) return dir === 'asc' ? -1 : 1
        if (va > vb) return dir === 'asc' ? 1 : -1
        return 0
      })
    },

    // 选择行变化
    handleSelectionChange(rows) {
      this.selectedRows = rows
    },

    // 加载表列表
    async loadTables() {
      try {
        const response = await axios.get('/api/tables')
        this.tables = response.data.tables
      } catch (error) {
        this.$message.error('加载表名失败: ' + error.message)
      }
    },

    // 进入表详情
    enterTable(row) {
      this.selectedTable = row.table_name
      this.currentColumns = row.columns || []
      this.pagination.page = 1
      this.sort.prop = null
      this.sort.order = null
      this.selectedRows = []
      this.loadConfigs()
    },

    // 返回概览
    backToOverview() {
      this.selectedTable = ''
      this.currentColumns = []
      this.configs = []
      this.selectedRows = []
    },

    // 排序改变
    handleSortChange({ prop, order }) {
      this.sort.prop = prop ? prop.replace('config_data.', '') : null
      this.sort.order = order === 'ascending' ? 'asc' : order === 'descending' ? 'desc' : null
      this.pagination.page = 1
      this.loadConfigs()
    },

    // 加载配置列表
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
        const response = await axios.get('/api/configs', { params })
        this.configs = response.data.configs
        this.pagination.total = response.data.total
        this.pagination.page = response.data.page

        // 从第一行数据刷新列（如果有新增列）
        if (this.configs.length > 0) {
          const keys = Object.keys(this.configs[0].config_data)
          if (keys.length !== this.currentColumns.length) {
            this.currentColumns = keys
          }
        }
      } catch (error) {
        this.$message.error('加载配置失败: ' + error.message)
      } finally {
        this.loading = false
      }
    },

    // 文件上传前验证
    beforeUpload(file) {
      const isMML = file.name.endsWith('.mml')
      if (!isMML) {
        this.$message.error('只能上传 .mml 文件!')
      }
      return isMML
    },

    // 上传成功
    handleUploadSuccess(response) {
      this.$message.success(response.message)
      this.loadTables()
      if (this.selectedTable) this.loadConfigs()
    },

    // 上传失败
    handleUploadError(error) {
      this.$message.error('上传失败: ' + error)
    },

    // 每页条数改变
    handleSizeChange(size) {
      this.pagination.pageSize = size
      this.pagination.page = 1
      this.loadConfigs()
    },

    // 分页改变
    handlePageChange(page) {
      this.pagination.page = page
      this.loadConfigs()
    },

    // ---- 批处理操作 ----

    // 批量删除
    async batchDelete() {
      if (this.selectedRows.length === 0) return
      this.$confirm(
        `确定要删除选中的 ${this.selectedRows.length} 条配置吗? 删除后不可恢复。`,
        '批量删除',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(async () => {
        try {
          const ids = this.selectedRows.map(r => r.id)
          await axios.post('/api/configs/batch-delete', {
            table_name: this.selectedTable,
            ids
          })
          this.$message.success(`成功删除 ${ids.length} 条配置`)
          this.selectedRows = []
          this.loadConfigs()
          this.loadTables()
        } catch (error) {
          this.$message.error('批量删除失败: ' + (error.response?.data?.error || error.message))
        }
      }).catch(() => {})
    },

    // 批量导出
    async batchExport() {
      if (this.selectedRows.length === 0) return
      try {
        const ids = this.selectedRows.map(r => r.id)
        const response = await axios.post('/api/export-mml', {
          table_name: this.selectedTable,
          ids
        })
        const blob = new Blob([response.data.content], { type: 'text/plain' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = response.data.filename
        a.click()
        window.URL.revokeObjectURL(url)
        this.$message.success(`成功导出 ${ids.length} 条配置`)
      } catch (error) {
        this.$message.error('导出失败: ' + (error.response?.data?.error || error.message))
      }
    },

    // 新增行对话框
    showAddRowDialog() {
      this.isNewRow = true
      this.editForm = {}
      this.currentColumns.forEach(col => {
        this.editForm[col] = ''
      })
      this.editDialogVisible = true
    },

    // 编辑配置
    handleEdit(row) {
      this.isNewRow = false
      this.editForm = { ...row.config_data }
      this.editForm._id = row.id
      this.editDialogVisible = true
    },

    // 保存编辑或新增
    async saveEdit() {
      try {
        const configData = {}
        this.currentColumns.forEach(col => {
          configData[col] = this.editForm[col] || ''
        })

        if (this.isNewRow) {
          await axios.post('/api/configs', {
            table_name: this.selectedTable,
            config_data: configData
          })
          this.$message.success('新增成功')
          this.editDialogVisible = false
          this.loadConfigs()
          this.loadTables()
          return
        }

        await axios.put(`/api/configs/${this.editForm._id}`, {
          table_name: this.selectedTable,
          config_data: configData
        })

        this.$message.success('保存成功')
        this.editDialogVisible = false
        this.loadConfigs()
      } catch (error) {
        this.$message.error('保存失败: ' + error.message)
      }
    },

    // 删除配置
    handleDelete(row) {
      this.$confirm('确定要删除这条配置吗? 删除后不可恢复。', '确认删除', {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          await axios.delete(`/api/configs/${row.id}`, {
            params: { table_name: this.selectedTable }
          })
          this.$message.success('删除成功')
          this.loadConfigs()
        } catch (error) {
          this.$message.error('删除失败: ' + error.message)
        }
      }).catch(() => {})
    }
  }
}
</script>

<style>
/* ====== 全局重置 ====== */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f5f7fa;
  color: #213547;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ====== 顶部导航（Vue.js 风格） ====== */
.vue-header {
  background: #1a1a2e;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px !important;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  flex-shrink: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 32px;
}

.header-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.vue-logo {
  flex-shrink: 0;
}

.header-title {
  font-size: 17px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.3px;
}

/* 顶部导航菜单 */
.vue-nav-menu.el-menu--horizontal {
  border-bottom: none !important;
}

.vue-nav-menu .el-menu-item {
  height: 56px;
  line-height: 56px;
  border-bottom: 2px solid transparent;
  font-size: 14px;
  padding: 0 16px;
  transition: border-color 0.2s, color 0.2s;
}

.vue-nav-menu .el-menu-item:hover {
  color: #fff !important;
  background: rgba(255,255,255,0.06) !important;
}

.vue-nav-menu .el-menu-item.is-active {
  color: #fff !important;
  border-bottom-color: #41b883 !important;
}

/* 头部右侧按钮组 */
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.vue-btn-outline {
  background: transparent !important;
  border: 1px solid rgba(255,255,255,0.25) !important;
  color: rgba(255,255,255,0.85) !important;
  transition: all 0.2s;
}

.vue-btn-outline:hover {
  border-color: #41b883 !important;
  color: #41b883 !important;
  background: rgba(65,184,131,0.08) !important;
}

.header-upload {
  display: inline-block;
}

/* GitHub 仓库链接 */
.github-link {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
  text-decoration: none;
}

.github-link:hover {
  background: rgba(255,255,255,0.1);
}

.github-link:hover svg {
  fill: #fff !important;
}

/* ====== 底部 Footer ====== */
.vue-footer {
  flex-shrink: 0;
  background: #1a1a2e;
  border-top: 1px solid rgba(255,255,255,0.06);
  padding: 14px 24px;
  text-align: center;
}

.footer-content {
  font-size: 12.5px;
  color: #888;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.footer-license {
  display: inline-flex;
  align-items: center;
  color: #999;
}

.footer-sep {
  color: #555;
}

.footer-copyright {
  color: #888;
}

/* 底部哨兵（触发 footer 显示） */
.footer-sentinel {
  height: 1px;
}

/* ====== 侧边栏（Vue.js 文档风格） ====== */
.vue-aside {
  background: #fff;
  border-right: 1px solid #e8e8e8;
  overflow-y: auto;
  transition: width 0.25s ease;
  flex-shrink: 0;
}

.aside-content {
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.aside-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
  margin-bottom: 16px;
}

.aside-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  display: flex;
  align-items: center;
  margin: 0;
}

.aside-section {
  margin-bottom: 20px;
}

.aside-section-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #999;
  margin-bottom: 10px;
}

.aside-column-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.aside-column-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 13px;
  color: #555;
  transition: background 0.15s;
}

.aside-column-item:hover {
  background: #f0f9f4;
}

.col-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #41b883;
  flex-shrink: 0;
}

.col-name {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 12.5px;
}

.aside-actions {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.aside-back-btn {
  width: 100%;
}

/* ====== 主体内容 ====== */
.vue-main {
  background: #f5f7fa;
  padding: 24px 32px;
  overflow-y: auto;
}

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
  color: #1a1a2e;
  margin: 0 0 6px 0;
  display: flex;
  align-items: center;
}

.page-desc {
  font-size: 14px;
  color: #888;
  margin: 0;
  line-height: 1.5;
}

.inline-code {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  background: #f0f0f0;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 12.5px;
  color: #476582;
}

/* ====== 卡片样式 ====== */
.filter-card {
  margin-bottom: 16px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
}

.data-card {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
}

.data-card .el-card__body {
  padding: 16px;
}

/* ====== 批处理工具栏 ====== */
.batch-toolbar {
  margin-bottom: 12px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  background: #fafbfc;
}

.batch-toolbar .el-card__body {
  padding: 12px 16px;
}

.batch-info {
  font-size: 13px;
  color: #555;
}

.batch-info strong {
  color: #e6a23c;
  font-size: 15px;
}

.vue-btn-outline-green {
  background: transparent !important;
  border: 1px solid #41b883 !important;
  color: #41b883 !important;
}

.vue-btn-outline-green:hover {
  background: rgba(65,184,131,0.08) !important;
  color: #2c9c6f !important;
  border-color: #2c9c6f !important;
}

.vue-btn-outline-green.is-disabled {
  border-color: #ddd !important;
  color: #ccc !important;
}

/* ====== 表格样式 ====== */
.el-table {
  border-radius: 6px;
}

.el-table th.el-table__cell {
  background: #f8f9fc !important;
  color: #555;
  font-weight: 600;
  font-size: 13px;
}

.el-table .cell {
  line-height: 1.5;
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
  background: #e8f5e9;
  color: #2e7d32;
}

.cell-value {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 12.5px;
  color: #333;
}

/* 分页 */
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* ====== 对话框 ====== */
.el-dialog__header {
  border-bottom: 1px solid #eee;
  padding: 16px 24px;
}

.el-dialog__title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
}

.el-dialog__body {
  padding: 20px 24px;
}

.el-dialog__footer {
  border-top: 1px solid #eee;
  padding: 12px 24px;
}

/* ====== Element UI 主题微调 ====== */
.el-button--success {
  background: #41b883;
  border-color: #41b883;
}

.el-button--success:hover {
  background: #3aa876;
  border-color: #3aa876;
}

.el-button--primary {
  background: #3eaf7c;
  border-color: #3eaf7c;
}

.el-button--primary:hover {
  background: #349b6b;
  border-color: #349b6b;
}

.el-button--primary.is-plain {
  color: #3eaf7c;
  background: #f0f9f4;
  border-color: #b8e6d0;
}

.el-button--primary.is-plain:hover {
  color: #2c9c6f;
  background: #d0f0e0;
  border-color: #8dd4b4;
}

.el-button--warning.is-plain {
  color: #e6a23c;
  background: #fdf6ec;
  border-color: #f5dab1;
}

/* 分页背景色 */
.el-pagination.is-background .el-pager li:not(.disabled).active {
  background: #41b883;
}

.el-pagination.is-background .el-pager li:not(.disabled):hover {
  color: #41b883;
}

/* Tag */
.el-tag--success.el-tag--dark {
  background: #41b883;
  border-color: #41b883;
}

/* 链接 */
.el-link.el-link--primary {
  color: #3eaf7c;
}

/* 输入框 focus */
.el-input__inner:focus {
  border-color: #41b883;
}

/* 滚动条 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #aaa;
}
</style>
