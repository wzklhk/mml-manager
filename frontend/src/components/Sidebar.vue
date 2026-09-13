<template>
  <div class="sidebar-wrapper">
    <el-aside :width="collapsed ? '0' : '260px'" class="vue-aside">
      <div v-if="!collapsed" class="aside-content">
        <!-- ====== Table list (overview mode) ====== -->
        <template v-if="!selectedTable">
          <div class="aside-header">
            <h3 class="aside-title">
              <i class="el-icon-menu" style="color: #41b883; margin-right: 6px"></i>
              {{ $t("sidebar.tables_title") || "Tables" }}
            </h3>
          </div>

          <div class="aside-section">
            <div class="aside-table-list">
              <div v-for="t in tables" :key="t.table_name" class="aside-table-item" @click="$emit('select-table', t)">
                <i
                  class="el-icon-s-data"
                  style="color: #41b883; font-size: 14px; margin-right: 6px; flex-shrink: 0"
                ></i>
                <span class="table-item-name">{{ t.table_name }}</span>
                <el-tag size="small" type="success" effect="dark" class="table-item-count">{{ t.count }}</el-tag>
              </div>
            </div>
            <el-pagination
              v-if="tablePagination.total > tablePagination.pageSize"
              class="aside-pagination"
              small
              background
              layout="prev, pager, next"
              :pager-count="5"
              :current-page="tablePagination.page"
              :page-size="tablePagination.pageSize"
              :total="tablePagination.total"
              @current-change="$emit('table-page-change', $event)"
            />
          </div>
        </template>

        <!-- ====== Column list (detail mode) ====== -->
        <template v-else>
          <div class="aside-header">
            <h3 class="aside-title">
              <i class="el-icon-s-grid" style="color: #41b883; margin-right: 6px"></i>
              {{ selectedTable }}
            </h3>
            <div class="aside-header-actions">
              <el-tag size="small" type="success" effect="dark">{{ totalRows }} {{ $t("sidebar.rows") }}</el-tag>
            </div>
          </div>

          <div class="aside-section">
            <div class="aside-section-title">{{ $t("sidebar.columns_title") }}</div>
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

    <div class="sidebar-toggle-rail">
      <button
        type="button"
        class="sidebar-edge-trigger"
        :title="collapsed ? $t('sidebar.expand') : $t('sidebar.collapse')"
        :aria-label="collapsed ? $t('sidebar.expand') : $t('sidebar.collapse')"
        @click="$emit('toggle-sidebar')"
      >
        <span aria-hidden="true">{{ collapsed ? "›" : "‹" }}</span>
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: "Sidebar",
  props: {
    selectedTable: { type: String, default: "" },
    tables: { type: Array, default: () => [] },
    columns: { type: Array, default: () => [] },
    totalRows: { type: Number, default: 0 },
    tablePagination: { type: Object, default: () => ({ page: 1, pageSize: 20, total: 0 }) },
    collapsed: { type: Boolean, default: false },
  },
};
</script>

<style scoped>
.sidebar-wrapper {
  position: relative;
  flex-shrink: 0;
  display: flex;
  flex-direction: row;
  min-width: 0;
  background: var(--sidebar-bg);
}

.vue-aside {
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border-color);
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

.aside-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
  margin-bottom: 16px;
  gap: 8px;
}

.aside-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
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

.aside-section {
  margin-bottom: 20px;
}
.aside-section-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
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
  color: var(--text-secondary);
  transition: background 0.15s;
}
.aside-column-item:hover {
  background: var(--hover-bg);
}
.col-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #41b883;
  flex-shrink: 0;
}
.col-name {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
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
  color: var(--text-primary);
  cursor: pointer;
  transition: background 0.15s;
  gap: 6px;
}
.aside-table-item:hover {
  background: var(--hover-bg);
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
.aside-pagination {
  margin-top: 14px;
  justify-content: center;
}

.sidebar-toggle-rail {
  flex: 0 0 28px;
  width: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
}

.sidebar-edge-trigger {
  flex: 0 0 auto;
  width: 24px;
  height: 48px;
  background: var(--sidebar-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 14px;
  z-index: 10;
  transition:
    color 0.15s,
    background 0.15s;
}

.sidebar-edge-trigger:hover {
  color: #41b883;
  background: var(--hover-bg);
}

.sidebar-edge-trigger:focus-visible {
  outline: 2px solid #41b883;
  outline-offset: 2px;
}
</style>
