<template>
  <div id="app">
    <el-container>
      <!-- 头部 -->
      <el-header>
        <h1>MML配置管理系统</h1>
      </el-header>

      <!-- 主体内容 -->
      <el-main>
        <!-- 操作栏 -->
        <el-card class="operation-card">
          <el-row :gutter="20">
            <el-col :span="5">
              <el-upload
                class="upload-demo"
                action="/api/import-mml"
                :on-success="handleUploadSuccess"
                :on-error="handleUploadError"
                :before-upload="beforeUpload"
                accept=".mml"
              >
                <el-button type="primary" icon="el-icon-upload">导入MML文件</el-button>
              </el-upload>
            </el-col>
            <el-col :span="5" v-if="selectedTable">
              <el-button type="success" icon="el-icon-download" @click="exportMML">导出MML</el-button>
            </el-col>
            <el-col :span="2" v-if="selectedTable">
              <el-button icon="el-icon-refresh" @click="loadConfigs">刷新</el-button>
            </el-col>
            <el-col :span="5" v-if="selectedTable && currentColumns.length > 0">
              <el-button type="warning" icon="el-icon-view" @click="showAddRowDialog">新增行</el-button>
            </el-col>
          </el-row>
        </el-card>

        <!-- ========== 所有表概览 ========== -->
        <el-card v-if="!selectedTable" class="table-card">
          <el-row :gutter="16">
            <el-col :span="8">
              <el-input
                v-model="tableSearch"
                placeholder="搜索表名..."
                prefix-icon="el-icon-search"
                clearable
              />
            </el-col>
            <el-col :span="16" style="text-align: right">
              <el-button icon="el-icon-refresh" size="small" @click="loadTables">刷新</el-button>
            </el-col>
          </el-row>
          <br>
          <el-table :data="filteredTables" style="width: 100%" border stripe>
            <el-table-column label="表名" min-width="200" sortable sort-by="table_name">
              <template slot-scope="scope">
                <el-link type="primary" @click="enterTable(scope.row)">
                  {{ scope.row.table_name }}
                </el-link>
              </template>
            </el-table-column>
            <el-table-column label="列" min-width="300">
              <template slot-scope="scope">
                <el-tag v-for="col in scope.row.columns" :key="col" size="small" style="margin: 2px">
                  {{ col }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="count" label="行数" width="100" sortable />
            <el-table-column prop="created_at" label="创建时间" width="180" sortable />
            <el-table-column label="操作" width="120">
              <template slot-scope="scope">
                <el-button size="mini" type="primary" @click="enterTable(scope.row)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- ========== 表详情（进入表后） ========== -->
        <el-card v-if="selectedTable" class="table-card">
          <template slot="header">
            <el-row>
              <el-col :span="12">
                <el-button icon="el-icon-arrow-left" size="small" @click="backToOverview">返回概览</el-button>
                <span style="margin-left: 12px; font-size: 16px; font-weight: bold;">
                  {{ selectedTable }} 表
                  <el-tag size="small" type="info">{{ pagination.total }} 行</el-tag>
                </span>
              </el-col>
              <el-col :span="12" style="text-align: right">
                <el-tag
                  v-for="col in currentColumns"
                  :key="col"
                  size="small"
                  type=""
                  style="margin: 0 2px"
                >{{ col }}</el-tag>
              </el-col>
            </el-row>
          </template>
          <el-table
            :data="configs"
            style="width: 100%"
            v-loading="loading"
            border
            stripe
            max-height="600"
            @sort-change="handleSortChange"
          >
            <el-table-column type="index" label="#" width="50" fixed="left" />
            <!-- 动态列 -->
            <el-table-column
              v-for="col in currentColumns"
              :key="col"
              :prop="'config_data.' + col"
              :label="col"
              sortable="custom"
              min-width="120"
            />
            <el-table-column label="操作" width="160" fixed="right">
              <template slot-scope="scope">
                <el-button size="mini" @click="handleEdit(scope.row)">编辑</el-button>
                <el-button size="mini" type="danger" @click="handleDelete(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <el-pagination
            @current-change="handlePageChange"
            @size-change="handleSizeChange"
            :current-page="pagination.page"
            :page-sizes="[10, 20, 50, 100]"
            :page-size="pagination.pageSize"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            style="margin-top: 20px; text-align: right"
          />
        </el-card>
      </el-main>
    </el-container>

    <!-- 编辑对话框 -->
    <el-dialog :title="isNewRow ? '新增行' : '编辑配置'" :visible.sync="editDialogVisible" width="50%">
      <el-form :model="editForm" label-width="120px">
        <!-- 动态字段：每个参数一个输入框 -->
        <el-form-item
          v-for="col in currentColumns"
          :key="col"
          :label="col"
        >
          <el-input v-model="editForm[col]" :placeholder="col" />
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">{{ isNewRow ? '新增' : '保存' }}</el-button>
      </span>
    </el-dialog>
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
    filteredTables() {
      if (!this.tableSearch) return this.tables
      const q = this.tableSearch.toLowerCase()
      return this.tables.filter(t => t.table_name.toLowerCase().includes(q))
    }
  },
  mounted() {
    this.loadTables()
  },
  methods: {
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
      this.loadConfigs()
    },

    // 返回概览
    backToOverview() {
      this.selectedTable = ''
      this.currentColumns = []
      this.configs = []
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
        this.$message.error('只能上传.mml文件!')
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
          const response = await axios.post('/api/configs', {
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
      this.$confirm('确定要删除这条配置吗?', '提示', {
        confirmButtonText: '确定',
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
    },

    // 导出MML
    async exportMML() {
      if (!this.selectedTable) {
        this.$message.warning('请先选择一个表')
        return
      }
      try {
        const response = await axios.post('/api/export-mml', {
          table_name: this.selectedTable
        })

        const blob = new Blob([response.data.content], { type: 'text/plain' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = response.data.filename
        a.click()
        window.URL.revokeObjectURL(url)

        this.$message.success('导出成功')
      } catch (error) {
        this.$message.error('导出失败: ' + error.message)
      }
    }
  }
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.el-header {
  background-color: #409EFF;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.el-header h1 {
  margin: 0;
  font-size: 24px;
}

.operation-card {
  margin-bottom: 20px;
}

.table-card {
  min-height: 400px;
}
</style>
