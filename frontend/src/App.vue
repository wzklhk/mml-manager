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
            <el-col :span="6">
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
            <el-col :span="6">
              <el-button type="success" icon="el-icon-download" @click="exportMML">导出MML</el-button>
            </el-col>
            <el-col :span="6">
              <el-select v-model="selectedTable" placeholder="选择表" clearable @change="loadConfigs">
                <el-option
                  v-for="table in tables"
                  :key="table"
                  :label="table"
                  :value="table"
                />
              </el-select>
            </el-col>
            <el-col :span="6">
              <el-button icon="el-icon-refresh" @click="loadConfigs">刷新</el-button>
            </el-col>
          </el-row>
        </el-card>

        <!-- 配置列表 -->
        <el-card class="table-card">
          <el-table
            :data="configs"
            style="width: 100%"
            v-loading="loading"
            border
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="table_name" label="表名" width="150" />
            <el-table-column prop="cmd_type" label="命令类型" width="100">
              <template slot-scope="scope">
                <el-tag :type="scope.row.cmd_type === 'ADD' ? 'success' : 'primary'">
                  {{ scope.row.cmd_type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="配置数据" min-width="300">
              <template slot-scope="scope">
                <el-popover trigger="hover" placement="top">
                  <pre>{{ JSON.stringify(scope.row.config_data, null, 2) }}</pre>
                  <div slot="reference" class="config-preview">
                    {{ formatConfigPreview(scope.row.config_data) }}
                  </div>
                </el-popover>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column label="操作" width="200" fixed="right">
              <template slot-scope="scope">
                <el-button size="mini" @click="handleEdit(scope.row)">编辑</el-button>
                <el-button size="mini" type="danger" @click="handleDelete(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <el-pagination
            @current-change="handlePageChange"
            :current-page="pagination.page"
            :page-size="pagination.pageSize"
            :total="pagination.total"
            layout="total, prev, pager, next"
            style="margin-top: 20px; text-align: right"
          />
        </el-card>
      </el-main>
    </el-container>

    <!-- 编辑对话框 -->
    <el-dialog title="编辑配置" :visible.sync="editDialogVisible" width="60%">
      <el-form :model="editForm" label-width="120px">
        <el-form-item label="表名">
          <el-input v-model="editForm.table_name" />
        </el-form-item>
        <el-form-item label="命令类型">
          <el-radio-group v-model="editForm.cmd_type">
            <el-radio label="SET">SET</el-radio>
            <el-radio label="ADD">ADD</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="配置数据">
          <el-input
            type="textarea"
            :rows="10"
            v-model="editForm.config_data_text"
            placeholder='例如: {"ID": "1", "NAME": "Cell_1"}'
          />
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
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
      loading: false,
      pagination: {
        page: 1,
        pageSize: 20,
        total: 0
      },
      editDialogVisible: false,
      editForm: {
        id: null,
        table_name: '',
        cmd_type: 'SET',
        config_data_text: ''
      }
    }
  },
  mounted() {
    this.loadTables()
    this.loadConfigs()
  },
  methods: {
    // 加载配置列表
    async loadConfigs() {
      this.loading = true
      try {
        const params = {
          page: this.pagination.page,
          page_size: this.pagination.pageSize
        }
        if (this.selectedTable) {
          params.table_name = this.selectedTable
        }
        
        const response = await axios.get('/api/configs', { params })
        this.configs = response.data.configs
        this.pagination.total = response.data.total
        this.pagination.page = response.data.page
      } catch (error) {
        this.$message.error('加载配置失败: ' + error.message)
      } finally {
        this.loading = false
      }
    },

    // 加载表名列表
    async loadTables() {
      try {
        const response = await axios.get('/api/tables')
        this.tables = response.data.tables
      } catch (error) {
        this.$message.error('加载表名失败: ' + error.message)
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
      this.loadConfigs()
    },

    // 上传失败
    handleUploadError(error) {
      this.$message.error('上传失败: ' + error)
    },

    // 分页改变
    handlePageChange(page) {
      this.pagination.page = page
      this.loadConfigs()
    },

    // 格式化配置预览
    formatConfigPreview(configData) {
      const keys = Object.keys(configData)
      if (keys.length === 0) return '{}'
      const preview = keys.slice(0, 3).map(key => `${key}=${configData[key]}`).join(', ')
      return keys.length > 3 ? preview + '...' : preview
    },

    // 编辑配置
    handleEdit(row) {
      this.editForm = {
        id: row.id,
        table_name: row.table_name,
        cmd_type: row.cmd_type,
        config_data_text: JSON.stringify(row.config_data, null, 2)
      }
      this.editDialogVisible = true
    },

    // 保存编辑
    async saveEdit() {
      try {
        let configData
        try {
          configData = JSON.parse(this.editForm.config_data_text)
        } catch (e) {
          this.$message.error('配置数据格式错误，请输入有效的JSON')
          return
        }

        await axios.put(`/api/configs/${this.editForm.id}`, {
          table_name: this.editForm.table_name,
          cmd_type: this.editForm.cmd_type,
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
          await axios.delete(`/api/configs/${row.id}`)
          this.$message.success('删除成功')
          this.loadConfigs()
        } catch (error) {
          this.$message.error('删除失败: ' + error.message)
        }
      }).catch(() => {})
    },

    // 导出MML
    async exportMML() {
      try {
        const response = await axios.post('/api/export-mml', {
          table_name: this.selectedTable || null
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
  min-height: 500px;
}

.config-preview {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
}

.config-preview:hover {
  color: #409EFF;
}
</style>
