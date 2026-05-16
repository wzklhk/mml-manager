<template>
  <el-aside :width="selectedTable ? '260px' : '0'" class="vue-aside">
    <div v-if="selectedTable" class="aside-content">
      <div class="aside-header">
        <h3 class="aside-title">
          <i class="el-icon-s-grid" style="color: #41b883; margin-right: 6px;"></i>
          {{ selectedTable }}
        </h3>
        <el-tag size="small" type="success" effect="dark">{{ totalRows }} 行</el-tag>
      </div>

      <div class="aside-section">
        <div class="aside-section-title">列</div>
        <div class="aside-column-list">
          <div v-for="col in columns" :key="col" class="aside-column-item">
            <span class="col-dot"></span>
            <span class="col-name">{{ col }}</span>
          </div>
        </div>
      </div>

      <div class="aside-actions">
        <el-button size="small" icon="el-icon-back" @click="$emit('back-to-overview')" class="aside-back-btn">
          返回概览
        </el-button>
      </div>
    </div>
  </el-aside>
</template>

<script>
export default {
  name: 'Sidebar',
  props: {
    selectedTable: { type: String, default: '' },
    columns: { type: Array, default: () => [] },
    totalRows: { type: Number, default: 0 }
  }
}
</script>

<style scoped>
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
.aside-section { margin-bottom: 20px; }
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
.aside-actions {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid #eee;
}
.aside-back-btn { width: 100%; }
</style>
