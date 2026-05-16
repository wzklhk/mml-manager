# MML 配置管理系统

MML (配置管理语言) 文件与表格格式 (Excel/CSV)、SQL、JSON 之间的双向转换工具集。提供 **CLI 命令行** 和 **Web UI** 两种使用方式。

## 快速开始

### 部署模式（前后端统一启动）

```bash
cd converter
source .venv/bin/activate
pip install -r requirements.txt

# 首次部署需要先构建前端
cd ../frontend && npm run build && cd ../converter

# 启动（自动加载前端静态文件+API）
python app.py
# 访问 http://localhost:5000
```

### 开发模式（前后端分离）

```bash
# 终端1：后端
cd converter && source .venv/bin/activate && python app.py

# 终端2：前端热重载
cd frontend && npm run serve
# 访问 http://localhost:8080（Vue proxy 自动转发 /api 到后端）
```

### 仅使用 CLI

```bash
cd converter && source .venv/bin/activate
python -m cli.to_sql input.mml -o output.sql
```

## 配置管理

通过 `config.yaml` 外置化配置，无需修改代码即可调整服务参数。

### config.yaml

创建于项目根目录 (`converter/config.yaml`)：

```yaml
server:
  host: 0.0.0.0       # 监听地址
  port: 5000           # 端口
  debug: true          # 调试模式

database:
  path: mml_config.db  # SQLite 数据库路径（相对路径基于 config.yaml 所在目录）

logging:
  level: INFO
```

### 配置搜索优先级

1. **环境变量 `MML_CONFIG_PATH`** — 指向自定义配置文件的路径
2. **项目目录 `./config.yaml`** — 与 `app.py` 同级的配置文件
3. **家目录 `~/.mml-manager/config.yaml`** — 全局配置
4. 以上均未找到时使用**硬编码默认值**

### 数据库路径

`database.path` 可以是相对路径（基于 `config.yaml` 所在目录）或绝对路径，数据库文件所在目录会自动创建。

## 部署

### 快速部署（单进程）

```bash
# 1. 构建前端
cd frontend && npm install && npm run build

# 2. 启动后端（自动加载 static/ 下的前端文件）
cd ../converter && source .venv/bin/activate && pip install -r requirements.txt
python app.py

# 访问 http://localhost:5000/   ← 页面 + API 同源，无跨域
```

生产环境建议用 gunicorn 或 uwsgi 替代 `python app.py`：

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

### 构建 & 部署要点

| 步骤 | 命令 | 说明 |
|:-----|:-----|:-----|
| 构建前端 | `cd frontend && npm run build` | 输出到 `converter/static/` |
| 启动后端 | `python app.py` | 自动提供前端 + API |
| 单机部署 | 仅需启动 Flask | 无需 Nginx 反代，无 CORS |

### 跨域说明

- **部署模式** (Flask 统一提供)：前端 /static + API /api 同域名同端口 → **无跨域问题**
- **开发模式** (npm run serve)：Vue CLI 的 `vue.config.js` 内置 proxy，自动转发 /api 到 Flask → **无跨域问题**

## 一键脚本

项目根目录的 `run.sh` 提供一键构建和启动：

```bash
cd mml-manager

# 一键部署（构建前端 → 启动服务）
./run.sh

# 仅构建前端
./run.sh build

# 仅启动后端（需先 build）
./run.sh start

# 开发模式（后端 5000 + 前端热重载 8080）
./run.sh dev
```

脚本自动检测 node/npm/python3 依赖、创建 venv 并安装依赖。

## 架构总览

```
project/
├── converter/                # 后端 (Flask + CLI)
│   ├── app.py               # ← Web 服务入口（统一提供前端 + API）
│   ├── config.yaml          #   外置化配置
│   ├── config.py            #   配置加载器
│   ├── static/              #   前端构建产物 (npm run build → 自动输出至此)
│   │   ├── index.html
│   │   ├── js/
│   │   └── css/
│   ├── cli/                 #   CLI 命令行入口
│   ├── controller/          #   API 路由层 (Controller)
│   ├── service/             #   业务逻辑层 (Service)
│   ├── dao/                 #   数据访问层 (DAO)
│   ├── converters/          #   转换核心
│   └── utils/               #   共享工具
│
└── frontend/                 # 前端 (Vue 2 + Element UI)
    ├── src/
    │   ├── App.vue           #   主页面（编排层：状态 + 事件分发）
    │   └── components/
    │       ├── VueHeader.vue      #   顶部导航栏（Logo/菜单/GitHub/导入）
    │       ├── Sidebar.vue        #   左侧边栏（表名/列列表/折叠按钮）
    │       ├── TableOverview.vue  #   表概览页（搜索 + 表格列表）
    │       ├── TableDetail.vue    #   表详情页（批处理栏 + 数据表 + 分页）
    │       ├── EditDialog.vue     #   编辑/新增对话框
    │       └── AppFooter.vue      #   底部（License/Copyright，滚动触发）
    └── vue.config.js         #   proxy 配置（仅开发模式使用）
```

## CLI 命令

所有 CLI 命令通过 `python -m cli.<模块名>` 调用。通用的 `-o` 指定输出路径，`--encoding` 指定编码。

### MML → SQL

```bash
python -m cli.to_sql input.mml -o output.sql
```

根据 MML 中的字段名自动推断 SQL 类型 (INTEGER / TEXT / REAL / BOOLEAN)，生成 `CREATE TABLE` + `INSERT INTO` 语句。

### SQL → MML

```bash
python -m cli.to_mml input.sql -o output.mml
```

自动检测 INSERT/SELECT 格式，解析并还原为 MML 命令。

### MML → JSON

```bash
python -m cli.to_json input.mml -o output.json
```

### JSON → MML

```bash
python -m cli.to_mml input.json -o output.mml
```

### MML → Excel

```bash
python -m cli.to_xls input.mml -o output.xlsx
python -m cli.to_xls input.mml               # 默认 output = input 前缀 + .xlsx
python -m cli.to_xls input.mml --csv         # 只生成 CSV
python -m cli.to_xls input.mml --both        # Excel + CSV 同时
```

- 每个 MML 表对应一个 Excel Sheet
- 表头带蓝色样式、自动列宽
- CSV 使用 UTF-8 BOM 编码（Excel 直接打开不乱码）

### Excel/CSV → MML

```bash
python -m cli.to_mml input.xlsx -o output.mml
python -m cli.to_mml data.csv -o output.mml --cmd ADD
python -m cli.to_mml input.xlsx --type tabular -o output_dir/   # 多表模式
```

参数：
- `--cmd SET|ADD` — 指定 MML 命令类型（默认 SET）
- `--type auto|sql|json|csv|xls|tabular` — 输入格式（默认自动检测）

### 完整工作流示例

```bash
# 1) MML → Excel
python -m cli.to_xls config.mml -o config.xlsx

# 2) 修改 Excel 后 → 转回 MML（回环验证）
python -m cli.to_mml config.xlsx -o roundtrip.mml

# 3) MML → SQL → 导入数据库
python -m cli.to_sql config.mml -o config.sql
sqlite3 mydb.db < config.sql

# 4) 从数据库导出 → MML
sqlite3 mydb.db "SELECT * FROM config;" --csv > data.csv
python -m cli.to_mml data.csv -o exported.mml
```

## Web UI 功能

进入表详情后可使用 **批处理操作**：

| 功能 | 说明 |
|:-----|:------|
| 复选框选择 | 勾选左侧复选框，工具栏显示选中数量 |
| [批量删除] | 确认后批量删除选中的行 |
| [批量添加] | 弹出表单新增一行 |
| [批量导出] | 将选中行导出为单独的 .mml 文件 |
| 侧栏折叠 | 点击 `◀` 按钮折叠左侧栏，折叠后 `▶` 标签可展开 |
| 滚动 Footer | 滚动到页面底部才显示 MIT License + Copyright |

## Web API

启动 Web 服务：

```bash
cd converter && source .venv/bin/activate
python app.py
```

访问 `http://localhost:5000`

### 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/import-mml` | 上传 MML 文件导入数据库 |
| GET | `/api/tables` | 获取所有 MML 表概览 |
| GET | `/api/configs?table_name=XXX&page=1&page_size=20` | 按表分页获取配置 |
| POST | `/api/configs` | 新增配置 (JSON body) |
| PUT | `/api/configs/<id>` | 更新配置 |
| DELETE | `/api/configs/<id>` | 删除配置 |
| POST | `/api/configs/batch-delete` | 批量删除配置 `{table_name, ids}` |
| POST | `/api/export-mml` | 导出为 MML（支持 `ids` 参数选中行） |

### 导入 MML 示例

```bash
curl -F "file=@config.mml" http://localhost:5000/api/import-mml
```

### 查询配置示例

```bash
# 获取所有表
curl http://localhost:5000/api/tables

# 分页查询指定表
curl "http://localhost:5000/api/configs?table_name=LTE_CELL&page=1&page_size=10"
```

## MML 文件格式

MML 文件使用 `SET`/`ADD` 命令描述配置数据，类似 SQL 注释风格：

```mml
-- LTE 小区配置
SET LTE_CELL:ID=1,NAME="Cell_A",PCI=100,BAND=3;
ADD LTE_CELL:ID=2,NAME="Cell_B",PCI=101,BAND=3;
```

- `SET` — 设置/覆盖配置
- `ADD` — 新增配置
- 值中的特殊字符（逗号、引号）使用 MML 三重引号格式 `"""值"""` 处理

## 依赖

| 包 | 用途 | 是否必需 |
|:---|:-----|:---------|
| `openpyxl` | Excel 读写 | CLI 转 XLS / Web API 导出必需 |
| `xlrd` | 旧版 .xls 读取 | 传统兼容，可选 |
| `lxml` | 部分旧版功能 | 可选 |
| `flask` + `flask-cors` | Web API 服务 | Web 模式必需 |
| `pyyaml` | 配置文件读取 | Web 模式必需 |
| `pytest` | 测试 | 开发用 |

## 设计原则

- **双向可逆**: 所有支持双向转换的格式均可做回环测试 (MML ⇄ Excel/CSV/SQL/JSON)
- **分层解耦**: Controller → Service → DAO 三层架构，转换核心封装在 `converters/` 包中
- **动态列存储**: Web API 使用 SQLite 动态列方案，每参数一列，便于 SQL 查询和前端展示
- **命令行统一**: 所有转换入口集中在 `cli/` 包，以 `python -m cli.<模块>` 方式调用

## 常见问题

**Q: Excel 转 MML 后，ADD 变成了 SET？**
由于 Excel/CSV 不记录命令类型，默认输出为 `SET`。使用 `--cmd ADD` 指定即可。

**Q: CSV 中的中文在 Excel 打开乱码？**
CSV 使用 UTF-8 BOM (`utf-8-sig`) 编码，Excel 可直接识别中文。

**Q: 值中含有逗号怎么办？**
脚本自动使用 MML 三重引号格式 (`"""值，含逗号"""`) 处理。
