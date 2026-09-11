<template>
  <el-dialog
    class="mml-ui"
    :model-value="visible"
    :title="$t('compare.title')"
    width="min(1040px, 92vw)"
    destroy-on-close
    @close="close"
  >
    <p class="compare-desc">{{ $t('compare.desc') }}</p>
    <div class="file-grid">
      <label class="file-box"
        ><span>{{ $t('compare.baseline') }}</span
        ><input type="file" accept=".mml,.txt" @change="selectFile('baseline', $event)" /><small>{{
          baseline ? baseline.name : $t('compare.no_file')
        }}</small></label
      >
      <label class="file-box"
        ><span>{{ $t('compare.target') }}</span
        ><input type="file" accept=".mml,.txt" @change="selectFile('target', $event)" /><small>{{
          target ? target.name : $t('compare.no_file')
        }}</small></label
      >
    </div>
    <div v-if="result" class="result-area">
      <div class="summary-grid">
        <div v-for="status in statuses" :key="status" :class="['summary-item', status]">
          <strong>{{ result.summary[status] }}</strong
          ><span>{{ $t('compare.' + status) }}</span>
        </div>
      </div>
      <el-collapse v-model="activeTables">
        <el-collapse-item v-for="table in changedTables" :key="table.table_name" :name="table.table_name">
          <template #title>
            <strong>{{ table.table_name }}</strong>
            <el-tag type="primary" size="small">+{{ table.summary.added }}</el-tag
            ><el-tag type="danger" size="small">-{{ table.summary.removed }}</el-tag
            ><el-tag type="warning" size="small">~{{ table.summary.modified }}</el-tag>
          </template>
          <el-alert v-if="table.warning" :title="table.warning" type="warning" :closable="false" show-icon />
          <div v-else class="key-hint">{{ $t('compare.key_field') }}: {{ table.key_fields.join(', ') }}</div>
          <el-table :data="table.diffs" border stripe max-height="360">
            <el-table-column :label="$t('compare.status')" width="90"
              ><template #default="scope"
                ><el-tag :type="tagType(scope.row.status)" size="small">{{
                  $t('compare.' + scope.row.status)
                }}</el-tag></template
              ></el-table-column
            >
            <el-table-column prop="key" :label="$t('compare.record')" min-width="180" />
            <el-table-column :label="$t('compare.details')" min-width="420"
              ><template #default="scope">
                <div v-if="scope.row.changes.length" class="change-list">
                  <div v-for="change in scope.row.changes" :key="change.field">
                    <code>{{ change.field }}</code
                    >: <del>{{ display(change.before) }}</del> → <ins>{{ display(change.after) }}</ins>
                  </div>
                </div>
                <pre v-else>{{ JSON.stringify(scope.row.after || scope.row.before, null, 2) }}</pre>
              </template></el-table-column
            >
          </el-table>
        </el-collapse-item>
      </el-collapse>
      <el-empty v-if="changedTables.length === 0" :description="$t('compare.no_changes')" />
    </div>
    <template #footer
      ><el-button @click="close">{{ $t('dialog.cancel') }}</el-button
      ><el-button type="primary" :loading="loading" :disabled="!baseline || !target" @click="compare">{{
        $t('compare.run')
      }}</el-button></template
    >
  </el-dialog>
</template>

<script>
import axios from 'axios'
export default {
  name: 'CompareDialog',
  props: { visible: { type: Boolean, default: false } },
  data: () => ({
    baseline: null,
    target: null,
    loading: false,
    result: null,
    activeTables: [],
    statuses: ['added', 'removed', 'modified', 'unchanged'],
  }),
  computed: {
    changedTables() {
      return this.result ? this.result.tables.filter((table) => table.diffs.length > 0) : []
    },
  },
  methods: {
    close() {
      this.$emit('update:visible', false)
    },
    selectFile(kind, event) {
      this[kind] = event.target.files?.[0] || null
      this.result = null
    },
    display(value) {
      return value === null || value === undefined || value === '' ? '∅' : String(value)
    },
    tagType(status) {
      return { added: 'success', removed: 'danger', modified: 'warning' }[status] || 'info'
    },
    async compare() {
      const form = new FormData()
      form.append('baseline', this.baseline)
      form.append('target', this.target)
      this.loading = true
      try {
        const response = await axios.post('/api/compare-mml', form)
        this.result = response.data
        this.activeTables = this.changedTables.slice(0, 1).map((table) => table.table_name)
      } catch (error) {
        this.$message.error(error.response?.data?.error || this.$t('compare.failed'))
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style scoped>
.compare-desc {
  margin: -8px 0 18px;
  color: var(--text-muted);
}
.file-grid,
.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
.file-box {
  padding: 16px;
  border: 1px dashed var(--border-color);
  border-radius: 8px;
  cursor: pointer;
}
.file-box span,
.file-box small {
  display: block;
}
.file-box span {
  margin-bottom: 10px;
  font-weight: 600;
}
.file-box small {
  margin-top: 8px;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.result-area {
  margin-top: 20px;
}
.summary-grid {
  grid-template-columns: repeat(4, 1fr);
  margin-bottom: 18px;
}
.summary-item {
  padding: 12px;
  border-radius: 8px;
  background: var(--bg-tertiary);
  text-align: center;
}
.summary-item strong,
.summary-item span {
  display: block;
}
.summary-item strong {
  font-size: 24px;
}
.summary-item span {
  font-size: 12px;
  color: var(--text-muted);
}
.added strong {
  color: #67c23a;
}
.removed strong {
  color: #f56c6c;
}
.modified strong {
  color: #e6a23c;
}
.unchanged strong {
  color: #909399;
}
.el-tag {
  margin-left: 8px;
}
.key-hint {
  margin: 0 0 10px;
  color: var(--text-muted);
  font-size: 12px;
}
.change-list {
  line-height: 1.8;
}
.change-list del {
  color: #f56c6c;
}
.change-list ins {
  color: #67c23a;
  text-decoration: none;
}
pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
}
@media (max-width: 720px) {
  .file-grid {
    grid-template-columns: 1fr;
  }
  .summary-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
