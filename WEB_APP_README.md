# MML配置管理Web系统

基于 Vue + ElementUI 前端和 Python Flask 后端的 MML 配置管理系统，支持 MML 文件的导入、解析、存储和 CRUD 操作。

## 项目结构

```
mml-manager/
├── converter/              # 后端（Flask）
│   ├── app.py             # Flask主应用
│   ├── utils/             # MML解析工具（复用现有模块）
│   ├── mml_config.db      # SQLite数据库（自动生成）
│   └── requirements.txt   # Python依赖
└── frontend/              # 前端（Vue + ElementUI）
    ├── src/
    │   ├── App.vue        # 主应用组件
    │   └── main.js        # 入口文件
    ├── public/
    │   └── index.html     # HTML模板
    ├── package.json       # Node.js依赖
    └── vue.config.js      # Vue CLI配置
```

## 功能特性

- ✅ **MML文件导入**：上传 .mml 文件自动解析并存储到数据库
- ✅ **配置列表展示**：分页显示所有配置，支持按表名筛选
- ✅ **CRUD操作**：查看、编辑、删除配置项
- ✅ **导出MML**：将数据库中的配置导出为 .mml 文件
- ✅ **实时预览**：鼠标悬停查看完整配置数据

## 快速开始

### 1. 安装后端依赖

```bash
cd converter
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
cd converter
python app.py
```

后端服务将在 `http://localhost:5000` 启动，自动创建 SQLite 数据库。

### 3. 安装前端依赖

```bash
cd frontend
npm install
```

### 4. 启动前端开发服务器

```bash
cd frontend
npm run serve
```

前端应用将在 `http://localhost:8080` 启动。

### 5. 访问系统

打开浏览器访问：`http://localhost:8080`

## API接口说明

### 健康检查
```
GET /api/health
```

### 导入MML文件
```
POST /api/import-mml
Content-Type: multipart/form-data
Body: file (MML文件)
```

### 获取配置列表
```
GET /api/configs?page=1&page_size=20&table_name=LTE_CELL
```

### 获取单个配置
```
GET /api/configs/{id}
```

### 更新配置
```
PUT /api/configs/{id}
Content-Type: application/json
Body: {
  "table_name": "LTE_CELL",
  "cmd_type": "SET",
  "config_data": {"ID": "1", "NAME": "Cell_1"}
}
```

### 删除配置
```
DELETE /api/configs/{id}
```

### 获取表名列表
```
GET /api/tables
```

### 导出MML文件
```
POST /api/export-mml
Content-Type: application/json
Body: {
  "table_name": "LTE_CELL"  // 可选，不传则导出全部
}
```

## 技术栈

### 后端
- **Python 3.x**
- **Flask**：Web框架
- **Flask-CORS**：跨域支持
- **SQLite**：轻量级数据库
- **openpyxl**：Excel处理（继承自原项目）

### 前端
- **Vue 2**：渐进式JavaScript框架
- **ElementUI**：UI组件库
- **Axios**：HTTP客户端
- **Vue CLI**：项目构建工具

## 数据库结构

### mml_configs 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| table_name | TEXT | 表名 |
| cmd_type | TEXT | 命令类型（SET/ADD） |
| config_data | TEXT | 配置数据（JSON格式） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## 使用示例

### 导入MML文件

1. 点击"导入MML文件"按钮
2. 选择 .mml 文件
3. 系统自动解析并显示导入结果

### 查看配置

- 在表格中查看所有配置
- 使用下拉框按表名筛选
- 鼠标悬停在配置数据上查看完整内容

### 编辑配置

1. 点击"编辑"按钮
2. 修改表名、命令类型或配置数据（JSON格式）
3. 点击"保存"

### 导出MML

1. （可选）选择要导出的表
2. 点击"导出MML"按钮
3. 浏览器自动下载 .mml 文件

## 常见问题

**Q: 前端无法连接后端？**
A: 确保后端服务已启动（http://localhost:5000），检查浏览器控制台是否有跨域错误。

**Q: 导入MML文件失败？**
A: 检查文件格式是否正确，确认文件中包含有效的 SET/ADD 命令。

**Q: 如何重置数据库？**
A: 删除 `converter/mml_config.db` 文件，重启后端服务会自动重建。

## 开发说明

### 后端开发

修改 `app.py` 后，Flask 的 debug 模式会自动重载服务。

### 前端开发

修改 `src/App.vue` 后，Vue CLI 的热更新会自动刷新浏览器。

### 生产部署

#### 后端
```bash
# 使用 Gunicorn 部署
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### 前端
```bash
npm run build
# 将 dist 目录部署到 Nginx 或其他静态服务器
```

## License

MIT
