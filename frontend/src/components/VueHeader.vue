<template>
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
        @select="$emit('menu-select', $event)"
        background-color="transparent"
        text-color="rgba(255,255,255,0.7)"
        active-text-color="#fff"
      >
        <el-menu-item index="overview">
          <i class="el-icon-menu"></i> 表概览
        </el-menu-item>
        <el-menu-item v-if="selectedTable" index="detail">
          <i class="el-icon-document"></i> {{ selectedTable }}
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
        :on-success="$emit('upload-success', $event)"
        :on-error="$emit('upload-error', $event)"
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
</template>

<script>
export default {
  name: 'VueHeader',
  props: {
    menuActive: { type: String, default: 'overview' },
    selectedTable: { type: String, default: '' }
  },
  methods: {
    beforeUpload(file) {
      if (!file.name.endsWith('.mml')) {
        this.$message.error('只能上传 .mml 文件!')
        return false
      }
      return true
    }
  }
}
</script>

<style scoped>
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
.vue-logo { flex-shrink: 0; }
.header-title {
  font-size: 17px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.3px;
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
  color: #fff !important;
  background: rgba(255,255,255,0.06) !important;
}
.vue-nav-menu .el-menu-item.is-active {
  color: #fff !important;
  border-bottom-color: #41b883 !important;
}
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
.header-upload { display: inline-block; }
.github-link {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
  text-decoration: none;
}
.github-link:hover { background: rgba(255,255,255,0.1); }
.github-link:hover svg { fill: #fff !important; }
</style>
