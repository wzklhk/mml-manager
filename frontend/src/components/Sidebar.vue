<template>
  <div class="sidebar-wrapper">
    <div v-if="collapsed" class="expand-trigger" @click="$emit('toggle-sidebar')" :title="$t('sidebar.expand')">
      <i class="el-icon-s-unfold"></i>
    </div>

    <el-aside :width="collapsed ? '0' : '260px'" class="vue-aside">
      <div v-if="!collapsed" class="aside-content">
        <!-- ====== Table list (overview mode) ====== -->
        <template v-if="!selectedTable">
          <div class="aside-header">
            <h3 class="aside-title">
              <i class="el-icon-menu" style="color: #41b883; margin-right: 6px;"></i>
              {{ $t('sidebar.tables_title') || 'Tables' }}
            </h3>
            <div class="aside-header-actions">
              <el-button
                size="small"
                circle
                class="collapse-btn"
                @click="$emit('toggle-sidebar')"
                :title="$t('sidebar.collapse')"
              >
                <i class="el-icon-d-arrow-left"></i>
              </el-button>
            </div>
          </div>

          <div class="aside-section">
            <div class="aside-table-list">
              <div
                v-for="t in tables"
                :key="t.table_name"
                class="aside-table-item"
                @click="$emit('select-table', t)"
              >
                <i class="el-icon-s-data" style="color: #41b883; font-size: 14px; margin-right: 6px; flex-shrink: 0;"></i>
                <span class="table-item-name">{{ t.table_name }}</span>
                <el-tag size="small" type="success" effect="dark" class="table-item-count">{{ t.count }}</el-tag>
              </div>
            </div>
          </div>
        </template>

        <!-- ====== Column list (detail mode) ====== -->
        <template v-else>
          <div class="aside-header">
            <h3 class="aside-title">
              <i class="el-icon-s-grid" style="color: #41b883; margin-right: 6px;"></i>
              {{ selectedTable }}
            </h3>
            <div class="aside-header-actions">
              <el-tag size="small" type="success" effect="dark">{{ totalRows }} {{ $t('sidebar.rows') }}</el-tag>
              <el-button
                size="small"
                circle
                class="collapse-btn"
                @click="$emit('toggle-sidebar')"
                :title="$t('sidebar.collapse')"
              >
                <i class="el-icon-d-arrow-left"></i>
              </el-button>
            </div>
          </div>

          <div class="aside-section">
            <div class="aside-section-title">{{ $t('sidebar.columns_title') }}</div>
            <div class="aside-column-list">
              <div v-for="col in columns" :key="col" class="aside-column-item">
                <span class="col-dot"></span>
                <span class="col-name">{{ col }}</span>
              </div>
            </div>
          </div>
        </template>
      </div>
    </el-aside>
  </div>
</template>

<script>
export default {
  name: 'Sidebar',
  props: {
    selectedTable: { type: String, default: '' },
    tables: { type: Array, default: () => [] },
    columns: { type: Array, default: () => [] },
    totalRows: { type: Number, default: 0 },
    collapsed: { type: Boolean, default: false }
  }
}
</script>

<style scoped>
.sidebar-wrapper {
  position: relative;
  flex-shrink: 0;
}

.vue-aside {
  background: #fff;
  border-right: 1px solid #e8e8e8;
  height: 100%;
  overflow: hidden;
  transition: width 0.25s ease;
  flex-shrink: 0;
}

.aside-content {
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 260px;
  overflow-y: auto;
}

.sidebar-wrapper {
  display: flex;
  flex-direction: column;
}

.aside-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
  margin-bottom: 16px;
  gap: 8px;
}

.aside-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  display: flex;
  align-items: center;
  margin: 0;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.aside-header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.collapse-btn {
  border: none !important;
  background: transparent !important;
  color: #999 !important;
  font-size: 13px;
  padding: 4px !important;
}

.collapse-btn:hover {
  background: #f0f0f0 !important;
  color: #555 !important;
}

.aside-section { margin-bottom: 20px; }
.aside-section-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #999;
  margin-bottom: 10px;
}

/* ---- Column list (detail mode) ---- */
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
.aside-column-item:hover { background: #f0f9f4; }
.col-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #41b883;
  flex-shrink: 0;
}
.col-name {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 12.5px;
}

/* ---- Table list (overview mode) ---- */
.aside-table-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.aside-table-item {
  display: flex;
  align-items: center;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 13px;
  color: #333;
  cursor: pointer;
  transition: background 0.15s;
  gap: 6px;
}
.aside-table-item:hover {
  background: #f0f9f4;
}
.table-item-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}
.table-item-count {
  flex-shrink: 0;
  font-size: 11px !important;
  padding: 0 5px !important;
  height: 18px !important;
  line-height: 18px !important;
}

.expand-trigger {
  position: absolute;
  top: 50%;
  right: -24px;
  transform: translateY(-50%);
  width: 24px;
  height: 48px;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-left: none;
  border-radius: 0 6px 6px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #999;
  font-size: 14px;
  z-index: 10;
  transition: color 0.15s, background 0.15s;
}

.expand-trigger:hover {
  color: #41b883;
  background: #f0f9f4;
}
</style>
