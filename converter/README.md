# MML 转换器

MML（配置管理语言）文件与表格格式（Excel/CSV）、SQL 之间的双向转换工具集。

## 项目结构

```
converter/
├── mml2tabular.py       # MML → Excel/CSV（主入口，合并 mml2xls + mml2sql）
├── tabular2mml.py       # Excel/CSV → MML
├── sql2mml.py           # SQL INSERT / SELECT → MML（支持数据库直连）
├── tabular.py           # Excel/CSV 读写核心模块（所有表格I/O集中管理）
├── cli_common.py        # 通用CLI参数、输出路径解析、文件校验
├── utils/
│   ├── __init__.py      # 公共导出入口
│   ├── table.py         # 数据模型：MmlConfig / TableGroup / MmlDataSet
│   ├── io_handler.py    # MML文件读写、统计输出、Banner打印
│   ├── mml.py           # MML值格式化与命令生成
│   ├── parse.py         # MML命令解析
│   └── sort.py          # 记录排序
├── _legacy/             # 旧版单用途脚本（已合并至上位脚本）
│   ├── mml2xls.py
│   ├── mml2sql.py
│   ├── xls2mml.py
│   └── csv2mml.py
├── requirements.txt
├── TEST_REPORT.md       # 最新测试报告
└── README.md
```

## 脚本说明

### 1. mml2tabular.py — MML → Excel/CSV

将 MML 配置文件（`SET`/`ADD` 命令）转换为表格格式。每个表对应一个 Sheet（Excel）或一个文件（CSV）。

```bash
# 默认生成 Excel (.xlsx)
python mml2tabular.py input.mml

# 只生成 CSV
python mml2tabular.py input.mml --csv

# 同时生成 Excel + CSV
python mml2tabular.py input.mml --both

# 指定输出前缀（不含扩展名）
python mml2tabular.py input.mml -o my_output

# 指定编码（默认 utf-8）
python mml2tabular.py input.mml --encoding gbk
```

**输出特性：**
- 每个表按 ID 升序排序
- Excel 表头带蓝色样式、自动列宽
- CSV 使用 UTF-8 BOM 编码（Excel 直接打开不乱码）
- 支持多表、中文、特殊字符（逗号/引号）

---

### 2. tabular2mml.py — Excel/CSV → MML

将表格文件（Excel/CSV）转换回 MML 配置命令。

```bash
# Excel 转 MML
python tabular2mml.py input.xlsx

# CSV 转 MML（指定输出路径）
python tabular2mml.py data.csv -o output.mml

# 指定 MML 命令类型（SET / ADD）
python tabular2mml.py data.csv --cmd ADD

# CSV 模式指定表名
python tabular2mml.py data.csv --table MY_TABLE

# 只读取特定 Sheet（Excel 模式）
python tabular2mml.py input.xlsx --sheets "LTE_CELL" "BOARD"

# 只提取指定字段
python tabular2mml.py input.xlsx --pick-fields ID NAME PCI

# 批量转换目录下所有 CSV
python tabular2mml.py ./csv_dir/ --batch
```

---

### 3. sql2mml.py — SQL → MML

从 SQL INSERT 语句或 SELECT 查询结果表格文本中解析数据，转换为 MML 格式。支持数据库直连。

```bash
# INSERT 语句解析（自动检测）
python sql2mml.py data.sql

# SELECT 结果表格解析
python sql2mml.py data.sql --format select

# 指定表名
python sql2mml.py data.sql --table LTE_CELL

# 数据库直连 — MySQL
python sql2mml.py --db mysql --db-host 10.0.0.1 --db-port 3306 \
    --db-user admin --db-pass secret --db-name mydb \
    --query "SELECT * FROM LTE_CELL"

# 数据库直连 — MongoDB
python sql2mml.py --db mongodb --db-uri "mongodb://..." \
    --db-name mydb --collection lte_cell

# 指定 MML 命令类型
python sql2mml.py data.sql --cmd ADD
```

**支持的 SQL 格式：**
- `INSERT INTO table (col1, col2) VALUES (val1, val2);`
- `INSERT table SET col1=val1, col2=val2;`
- `SELECT` 查询结果表格文本（含格式化表头）
- MySQL / MongoDB 数据库直连

---

## 快速入门

### 1. 环境搭建

```bash
cd converter
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
# .venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### 2. 完整工作流示例

```bash
# 1) MML → Excel
python mml2tabular.py my_config.mml -o output

# 2) 验证：Excel → MML 回环检查
python tabular2mml.py output.xlsx -o roundtrip.mml
diff my_config.mml roundtrip.mml   # 应匹配（顺序可能不同）

# 3) MML → CSV
python mml2tabular.py my_config.mml --csv

# 4) SQL → MML
python sql2mml.py data.sql
```

### 3. 运行测试

```bash
# 使用 pytest 运行单元测试（如有）
pytest

# 或手动回环测试
python mml2tabular.py test_sample.mml -o test.xlsx
python tabular2mml.py test.xlsx -o test_rt.mml
```

## 依赖说明

| 包 | 用途 | 备注 |
|:---|:-----|:-----|
| `openpyxl` | Excel 读写 | `mml2tabular`, `tabular2mml` 必需 |
| `xlrd` | 旧版 Excel (.xls) 读取 | 传统兼容 |
| `lxml` | XML/MathML 生成 | `sql2mml` 部分功能 |
| `pymongo` | MongoDB 直连 | 仅 `sql2mml --db mongodb` |
| `pymysql` | MySQL 直连 | 仅 `sql2mml --db mysql` |

## 设计原则

- **双向可逆**: 所有转换均支持回环测试（MML ⇄ Excel/CSV），确保无损
- **集中I/O**: 所有表格格式的读写集中在 `tabular.py`，便于扩展新格式（如 ODS）
- **共享模型**: 统一使用 `MmlDataSet` / `MmlConfig` 数据模型，降低耦合
- **渐进式**: 旧版脚本保留在 `_legacy/` 目录，新功能优先扩展主入口脚本

## 常见问题

**Q: Excel 转 MML 后，`ADD` 变成了 `SET`？**
由于 Excel/CSV 不记录命令类型，默认输出为 `SET`。使用 `--cmd ADD` 指定即可。

**Q: CSV 中的中文在 Excel 打开乱码？**
CSV 使用 UTF-8 BOM (`utf-8-sig`) 编码，Excel 可直接识别中文。

**Q: 值中含有逗号怎么办？**
脚本自动使用 MML 三重引号格式（`"""值，含逗号"""`）处理。
