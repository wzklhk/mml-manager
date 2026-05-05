# 快速开始指南

## 方式一：使用启动脚本（推荐）

双击运行 `start.bat`，系统会自动启动前后端服务。

## 方式二：手动启动

### 1. 启动后端

```bash
cd converter
pip install -r requirements.txt
python app.py
```

后端将在 http://localhost:5000 启动

### 2. 启动前端（新终端窗口）

```bash
cd frontend
npm install
npm run serve
```

前端将在 http://localhost:8080 启动

### 3. 访问系统

打开浏览器访问：http://localhost:8080

## 测试流程

1. **导入MML文件**
   - 点击"导入MML文件"按钮
   - 选择项目根目录下的 `test_sample.mml` 文件
   - 查看导入成功的提示

2. **查看配置**
   - 在表格中查看所有配置数据
   - 使用下拉框筛选特定表（如 LTE_CELL）
   - 鼠标悬停查看完整配置内容

3. **编辑配置**
   - 点击任意行的"编辑"按钮
   - 修改配置数据（JSON格式）
   - 点击保存

4. **删除配置**
   - 点击"删除"按钮
   - 确认删除操作

5. **导出MML**
   - （可选）选择要导出的表
   - 点击"导出MML"按钮
   - 浏览器自动下载 .mml 文件

## 常见问题

### Q: npm install 很慢？
A: 可以使用淘宝镜像：
```bash
npm config set registry https://registry.npmmirror.com
npm install
```

### Q: 端口被占用？
A: 
- 后端：修改 `app.py` 中的 `port=5000` 为其他端口
- 前端：修改 `vue.config.js` 中的 `port: 8080` 为其他端口

### Q: 前端无法连接后端？
A: 
1. 确认后端已启动（访问 http://localhost:5000/api/health）
2. 检查浏览器控制台是否有错误
3. 确认防火墙未阻止连接

## 下一步

- 查看 [WEB_APP_README.md](WEB_APP_README.md) 了解详细功能
- 查看 [converter/README.md](converter/README.md) 了解命令行工具用法
