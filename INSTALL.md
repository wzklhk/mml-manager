# 安装和运行指南

## 📋 前置要求

- **Python 3.6+** - [下载地址](https://www.python.org/downloads/)
- **Node.js 14+** - [下载地址](https://nodejs.org/)
- **npm** - 随 Node.js 一起安装

## 🔧 安装步骤

### 方法一：一键启动（Windows，推荐）

```bash
双击运行 start.bat
```

脚本会自动：
1. ✅ 检查 Python 环境
2. ✅ 启动后端服务（新窗口）
3. ✅ 安装前端依赖（首次运行）
4. ✅ 启动前端服务（新窗口）

### 方法二：手动安装

#### Step 1: 安装后端依赖

```bash
cd converter
pip install -r requirements.txt
```

预期输出：
```
Successfully installed flask-2.x.x flask-cors-3.x.x ...
```

#### Step 2: 启动后端

```bash
python app.py
```

预期输出：
```
[OK] 数据库初始化完成: ...\mml_config.db

============================================================
MML配置管理Web服务启动中...
============================================================
API地址: http://localhost:5000
数据库: ...\mml_config.db
============================================================

 * Running on http://0.0.0.0:5000
```

**保持这个窗口打开！**

#### Step 3: 安装前端依赖（新终端窗口）

```bash
cd frontend
npm install
```

预期输出：
```
added xxx packages in xx s
```

如果下载慢，使用国内镜像：
```bash
npm config set registry https://registry.npmmirror.com
npm install
```

#### Step 4: 启动前端

```bash
npm run serve
```

预期输出：
```
App running at:
  - Local:   http://localhost:8080/
  - Network: http://192.168.x.x:8080/
```

**保持这个窗口打开！**

#### Step 5: 访问系统

打开浏览器访问：**http://localhost:8080**

## 🎯 首次使用

### 1. 导入测试数据

1. 点击页面顶部的 **"导入MML文件"** 按钮
2. 选择项目根目录下的 `test_sample.mml` 文件
3. 等待上传完成，看到成功提示

### 2. 查看配置

- 表格自动显示所有配置
- 使用下拉框筛选特定表（如 LTE_CELL、BOARD 等）
- 鼠标悬停在"配置数据"列查看完整内容

### 3. 编辑配置

1. 点击任意行的 **"编辑"** 按钮
2. 修改表单中的内容：
   - 表名：如 `LTE_CELL`
   - 命令类型：SET 或 ADD
   - 配置数据：JSON 格式，如 `{"ID": "1", "NAME": "Cell_01"}`
3. 点击 **"保存"**

### 4. 删除配置

1. 点击 **"删除"** 按钮
2. 在确认对话框中点击 **"确定"**

### 5. 导出MML

1. （可选）从下拉框选择要导出的表
2. 点击 **"导出MML"** 按钮
3. 浏览器自动下载 `.mml` 文件

## 🔍 验证安装

### 检查后端

浏览器访问：http://localhost:5000/api/health

应返回：
```json
{
  "status": "ok",
  "timestamp": "2026-05-06T01:47:44.xxx"
}
```

### 检查前端

浏览器访问：http://localhost:8080

应看到：
- 蓝色标题栏："MML配置管理系统"
- 操作按钮：导入、导出、刷新
- 空表格或已导入的配置列表

## ❓ 故障排查

### 问题1：pip install 失败

**症状**：`Command 'pip' not found`

**解决**：
```bash
# Windows
python -m pip install -r requirements.txt

# 或使用完整路径
C:\Python39\Scripts\pip.exe install -r requirements.txt
```

### 问题2：npm install 卡住

**症状**：长时间停留在 `fetchMetadata` 或 `resolveTree`

**解决**：
```bash
# 清除缓存
npm cache clean --force

# 使用淘宝镜像
npm config set registry https://registry.npmmirror.com

# 重新安装
npm install
```

### 问题3：端口被占用

**症状**：`OSError: [Errno 98] Address already in use`

**解决**：

后端端口修改（app.py）：
```python
app.run(host='0.0.0.0', port=5001, debug=True)  # 改为 5001
```

前端端口修改（vue.config.js）：
```javascript
devServer: {
  port: 8081,  // 改为 8081
  ...
}
```

### 问题4：跨域错误

**症状**：浏览器控制台显示 CORS 错误

**解决**：
1. 确认后端已启动
2. 检查 `app.py` 中包含 `CORS(app)`
3. 重启后端服务

### 问题5：数据库文件不存在

**症状**：`sqlite3.OperationalError: no such table`

**解决**：
```bash
# 删除旧数据库
del converter\mml_config.db

# 重启后端，会自动重建
python app.py
```

### 问题6：Vue 编译错误

**症状**：`Module not found: Error: Can't resolve 'element-ui'`

**解决**：
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 🛠️ 开发模式

### 后端热重载

Flask 的 debug 模式已启用，修改 `app.py` 后会自动重启。

### 前端热更新

Vue CLI 的热更新已启用，修改 `src/App.vue` 后浏览器会自动刷新。

## 📦 生产部署

### 后端部署

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动（4个工作进程）
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 前端部署

```bash
# 构建生产版本
npm run build

# dist 目录部署到 Nginx
# Nginx 配置示例：
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/dist;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:5000;
    }
}
```

## 📞 获取帮助

如果遇到问题：

1. 查看控制台错误信息
2. 检查后端日志（启动 Flask 的终端窗口）
3. 查阅 [WEB_APP_README.md](WEB_APP_README.md)
4. 查阅 [QUICKSTART.md](QUICKSTART.md)

## 🎉 开始使用

一切就绪后，访问 http://localhost:8080 开始使用 MML 配置管理系统！

祝使用愉快！🚀
