# MML 转换器

本目录包含用于处理 MML（配置管理语言）文件的各种转换脚本。

## 脚本列表

### 数据转换

### 辅助工具

## 环境搭建

1. 创建虚拟环境（推荐）：

   ```bash
   python -m venv .venv
   ```

2. 激活虚拟环境：
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`

3. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

## 依赖说明

- `openpyxl` / `xlrd`: Excel 文件解析
- `lxml`: XML/MathML 生成
- `pymongo` / `pymysql`: 数据库连接（如使用 SQL 相关功能）
