# MML 配置管理系统

MML 配置文件与 Excel/CSV/SQL/JSON 之间的双向转换工具，带 Web UI。

## 快速上手

```bash
# 一键构建 + 启动
./run.sh

# 或者分步操作
cd frontend && npm install && npm run build
cd ../converter && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && python app.py

# 访问 http://localhost:5000
```

## 项目结构

```
├── run.sh          一键构建 & 启动脚本
├── converter/      后端 (Flask + CLI + Web UI)
│   └── README.md   详细文档（架构、API、配置、部署）
└── frontend/       前端 (Vue 2 + Element UI)
```

详细信息请参阅 [converter/README.md](converter/README.md)。
