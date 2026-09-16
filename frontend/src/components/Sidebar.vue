<template>
  <div class="sidebar-wrapper" :class="{ resizing }">
    <el-aside :width="collapsed ? '0' : `${sidebarWidth}px`" class="vue-aside">
      <div v-if="!collapsed" class="aside-content">
        <div class="aside-header">
          <h3 class="aside-title">
            <i class="el-icon-menu" style="color: #41b883; margin-right: 6px"></i>
            {{ $t("sidebar.tables_title") || "Tables" }}
          </h3>
        </div>

        <el-input
          v-model="tableSearch"
          class="aside-table-search"
          :placeholder="$t('sidebar.search_placeholder')"
          clearable
        />

        <div class="aside-section">
          <div class="aside-table-list">
            <div
              v-for="t in filteredTables"
              :key="t.table_name"
              class="aside-table-item"
              :class="{ active: t.table_name === selectedTable }"
              :aria-current="t.table_name === selectedTable ? 'page' : undefined"
              @click="$emit('select-table', t)"
            >
              <i class="el-icon-s-data" style="color: #41b883; font-size: 14px; margin-right: 6px; flex-shrink: 0"></i>
              <span class="table-item-name">{{ t.table_name }}</span>
              <el-tag size="small" type="success" effect="dark" class="table-item-count">{{ t.count }}</el-tag>
            </div>
          </div>
        </div>
      </div>
    </el-aside>

    <div
      v-if="!collapsed"
      class="sidebar-resizer"
      :class="{ active: resizing }"
      role="separator"
      aria-orientation="vertical"
      :aria-label="$t('sidebar.resize')"
      :aria-valuemin="minSidebarWidth"
      :aria-valuemax="maxSidebarWidth"
      :aria-valuenow="sidebarWidth"
      tabindex="0"
      @pointerdown="beginResize"
      @keydown="resizeWithKeyboard"
    ></div>

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
const MIN_SIDEBAR_WIDTH = 140;
const MAX_SIDEBAR_WIDTH = 480;
const MAIN_CONTENT_MIN_WIDTH = 320;

export default {
  name: "Sidebar",
  props: {
    selectedTable: { type: String, default: "" },
    tables: { type: Array, default: () => [] },
    collapsed: { type: Boolean, default: false },
  },
  data() {
    return {
      tableSearch: "",
      sidebarWidth: 260,
      minSidebarWidth: MIN_SIDEBAR_WIDTH,
      maxSidebarWidth: MAX_SIDEBAR_WIDTH,
      resizing: false,
      resizeStartX: 0,
      resizeStartWidth: 0,
      previousBodyCursor: "",
      previousBodyUserSelect: "",
    };
  },
  computed: {
    filteredTables() {
      const query = this.tableSearch.trim().toLocaleLowerCase();
      if (!query) return this.tables;
      return this.tables.filter((table) => String(table.table_name).toLocaleLowerCase().includes(query));
    },
  },
  watch: {
    collapsed(value) {
      if (value) this.endResize();
    },
  },
  mounted() {
    this.updateResizeBounds();
    window.addEventListener("resize", this.updateResizeBounds);
  },
  beforeUnmount() {
    this.endResize();
    window.removeEventListener("resize", this.updateResizeBounds);
  },
  methods: {
    clampSidebarWidth(width) {
      return Math.min(this.maxSidebarWidth, Math.max(this.minSidebarWidth, width));
    },
    updateResizeBounds() {
      const availableWidth = this.$el?.parentElement?.clientWidth || window.innerWidth;
      this.maxSidebarWidth = Math.max(
        this.minSidebarWidth,
        Math.min(MAX_SIDEBAR_WIDTH, availableWidth - MAIN_CONTENT_MIN_WIDTH),
      );
      this.sidebarWidth = this.clampSidebarWidth(this.sidebarWidth);
    },
    beginResize(event) {
      if (this.collapsed || event.button !== 0) return;
      event.preventDefault();
      this.updateResizeBounds();
      this.resizing = true;
      this.resizeStartX = event.clientX;
      this.resizeStartWidth = this.sidebarWidth;
      this.previousBodyCursor = document.body.style.cursor;
      this.previousBodyUserSelect = document.body.style.userSelect;
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
      window.addEventListener("pointermove", this.handleResize);
      window.addEventListener("pointerup", this.endResize);
      window.addEventListener("pointercancel", this.endResize);
    },
    handleResize(event) {
      if (!this.resizing) return;
      event.preventDefault();
      this.sidebarWidth = this.clampSidebarWidth(this.resizeStartWidth + event.clientX - this.resizeStartX);
    },
    endResize() {
      if (!this.resizing) return;
      this.resizing = false;
      document.body.style.cursor = this.previousBodyCursor;
      document.body.style.userSelect = this.previousBodyUserSelect;
      window.removeEventListener("pointermove", this.handleResize);
      window.removeEventListener("pointerup", this.endResize);
      window.removeEventListener("pointercancel", this.endResize);
    },
    resizeWithKeyboard(event) {
      const step = event.shiftKey ? 32 : 16;
      const nextWidths = {
        ArrowLeft: this.sidebarWidth - step,
        ArrowRight: this.sidebarWidth + step,
        Home: this.minSidebarWidth,
        End: this.maxSidebarWidth,
      };
      if (!(event.key in nextWidths)) return;
      event.preventDefault();
      this.sidebarWidth = this.clampSidebarWidth(nextWidths[event.key]);
    },
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
.sidebar-wrapper.resizing .vue-aside {
  transition: none;
}

.aside-content {
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
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

.aside-section {
  margin-bottom: 20px;
}

.aside-table-search {
  margin-bottom: 12px;
}

/* ---- Table list ---- */
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
.aside-table-item.active {
  color: #2f855a;
  background: color-mix(in srgb, #41b883 14%, transparent);
  box-shadow: inset 3px 0 0 #41b883;
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
.sidebar-resizer {
  position: relative;
  z-index: 20;
  flex: 0 0 8px;
  width: 8px;
  margin: 0 -4px;
  cursor: col-resize;
  touch-action: none;
}
.sidebar-resizer::before {
  content: "";
  position: absolute;
  inset: 0 3px;
  background: transparent;
  transition: background 0.15s ease;
}
.sidebar-resizer:hover::before,
.sidebar-resizer:focus-visible::before,
.sidebar-resizer.active::before {
  background: #41b883;
}
.sidebar-resizer:focus-visible {
  outline: 2px solid #41b883;
  outline-offset: -2px;
}
.sidebar-toggle-rail {
  flex: 0 0 28px;
  width: 28px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  background: var(--bg-primary);
}

.sidebar-edge-trigger {
  flex: 0 0 auto;
  width: 24px;
  height: 48px;
  background: var(--sidebar-bg);
  border: 1px solid var(--border-color);
  border-left: 0;
  border-radius: 0 6px 6px 0;
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
