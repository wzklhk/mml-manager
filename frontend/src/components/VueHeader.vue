<template>
  <el-header class="vue-header">
    <div class="header-left">
      <el-button text @click="$emit('menu-select', 'overview')">{{ $t('header.table_overview') }}</el-button>
      <span v-if="selectedTable" class="selected-table-name">{{ selectedTable }}</span>
    </div>
    <div class="header-right">
      <el-select
        v-if="snapshots.length"
        :model-value="activeSnapshotId"
        class="snapshot-select"
        size="small"
        :placeholder="$t('header.select_config')"
        @change="$emit('snapshot-change', $event)"
      >
        <el-option v-for="item in snapshots" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-button size="small" type="primary" plain @click="$emit('compare')">{{ $t('header.compare_mml') }}</el-button>
      <el-upload
        class="header-upload"
        action="/api/import-mml"
        @success="(r) => $emit('upload-success', r)"
        @error="(e) => $emit('upload-error', e)"
        :before-upload="beforeUpload"
        accept=".mml,.txt"
        :show-file-list="false"
      >
        <el-button size="small" class="vue-btn-outline">
          <i class="el-icon-upload2"></i> {{ $t('header.import_mml') }}
        </el-button>
      </el-upload>
    </div>
  </el-header>
</template>

<script>
export default {
  name: 'VueHeader',
  props: {
    menuActive: { type: String, default: 'overview' },
    selectedTable: { type: String, default: '' },
    snapshots: { type: Array, default: () => [] },
    activeSnapshotId: { type: String, default: '' }
  },
  methods: {
    beforeUpload(file) {
      if (!['.mml', '.txt'].some(ext => file.name.toLowerCase().endsWith(ext))) {
        this.$message.error(this.$t('header.only_mml_file'))
        return false
      }
      this.$emit('upload-start')
      return true
    }
  }
}
</script>

<style scoped>
.vue-header {
  background: var(--header-bg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  min-height: 56px;
  height: auto !important;
  flex-wrap: wrap;
  gap: 8px;
  padding-top: 6px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--header-border);
  flex-shrink: 0;
  z-index: 100;
  transition: background 0.3s;
}
.selected-table-name { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; }
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.header-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}
.vue-logo { flex-shrink: 0; }
.header-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--header-text-active);
  letter-spacing: 0.3px;
  transition: color 0.3s;
}
.vue-nav-menu.el-menu--horizontal { border-bottom: none !important; }
.vue-nav-menu .el-menu-item {
  height: 56px;
  line-height: 56px;
  border-bottom: 2px solid transparent;
  font-size: 14px;
  padding: 0 16px;
  transition: border-color 0.2s, color 0.2s;
}
.vue-nav-menu .el-menu-item:hover {
  color: var(--header-text-active) !important;
  background: var(--header-btn-bg-hover) !important;
}
.vue-nav-menu .el-menu-item.is-active {
  color: var(--header-text-active) !important;
  border-bottom-color: #41b883 !important;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.snapshot-select { width: 220px; margin-right: 6px; }

/* ---- Upload button ---- */
.vue-btn-outline {
  background: transparent !important;
  border: 1px solid var(--header-btn-border) !important;
  color: var(--header-text) !important;
  transition: all 0.2s;
}
.vue-btn-outline:hover {
  border-color: #41b883 !important;
  color: #41b883 !important;
  background: rgba(65,184,131,0.08) !important;
}
.header-upload { display: inline-block; }

</style>
