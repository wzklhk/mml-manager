# MML Manager

面向核心网网元配置运维的本地 B/S 工具，用于整理、检索、转换和对比复杂的 MML 配置。

## 功能摘要

- 转换器与 CLI：MML 与 Excel、CSV、SQL、JSON 双向转换
- Web 界面支持导入 MML/TXT、CSV 和 Excel（`.xlsx`）；Excel 保留原生单元格类型，CSV 自动识别 JSON 标量并将 `001` 等前导零值保留为字符串
- 配置表查询、按列筛选、排序、分页和编辑；常用字段可固定到表格左侧
- 支持将选中配置、当前命令表或全部配置导出为 MML、CSV、Excel
- 基线与现网 MML 的新增、删除、修改及字段级对比
- 完整解析 `ADD`/`SET`，兼容含空格命令名、单双引号值、UTF-8 与 GB18030
- 导入会按网元/文件创建彼此隔离、可切换和删除的 SQLite 配置集；查看、编辑、删除和导出均操作当前配置集
- 配置集、编辑结果及当前活动配置均持久化到 SQLite，服务重启后可恢复
- 查询采用有容量上限的进程内 LRU 缓存，未命中时读取 SQLite；写操作同步更新数据库并刷新相关缓存
- Vue 3 + Element Plus 界面，支持中英文、明暗主题和模块化工作台

## 快速启动

要求已安装 Python 3、Node.js 和 npm。在项目根目录运行：

```powershell
# Windows PowerShell
.\run.ps1
```

```bash
# Linux / macOS
chmod +x run.sh
./run.sh
```

无参数运行脚本时，每次都会执行 `npm run build` 重新打包前端，然后启动 FastAPI。启动后访问 `http://localhost:5000`。

前端没有变化且已有 `backend/src/app/static` 构建产物时，可使用 `.\run.ps1 start` 或 `./run.sh start` 跳过打包；日常开发使用 `.\run.ps1 dev` 或 `./run.sh dev`，由 Vite 提供热更新。

更多启动方式、环境配置和 API 地址见 Wiki 的[快速开始](https://github.com/wzklhk/mml-manager/wiki/Getting-Started)。

## 命令行转换

后端命令行工具无需启动 Web 服务，可直接将 MML 文件转换为 Excel/CSV 表格、JSON、SQL 脚本或 SQLite 数据库。首次使用时安装后端及其依赖：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Linux/macOS 将激活命令替换为 `source .venv/bin/activate`。以下命令均在 `backend` 目录中执行。

转换为 Excel 表格：

```powershell
python -m app.cli.to_xls ..\data\config.mml
```

只生成 CSV，或同时生成 Excel 和 CSV：

```powershell
python -m app.cli.to_xls ..\data\config.mml --csv
python -m app.cli.to_xls ..\data\config.mml --both -o ..\data\config-table
```

转换为 JSON：

```powershell
python -m app.cli.to_json ..\data\config.mml -o ..\data\config.json
```

同时生成 SQL 脚本和 SQLite 数据库：

```powershell
python -m app.cli.to_sql ..\data\config.mml -o ..\data\config.sql -d config.db
```

输入文件默认按 UTF-8 读取；GB18030/GBK 文件可添加 `--encoding gb18030` 或 `--encoding gbk`。省略 `-o` 时，输出默认与输入文件同目录、同名。更多参数见 Wiki 的[命令行转换](https://github.com/wzklhk/mml-manager/wiki/Command-Line-Conversion)，或运行 `python -m app.cli.to_sql --help`。

## 文档

完整的使用、架构、接口和实现文档统一维护在 [MML Manager Wiki](https://github.com/wzklhk/mml-manager/wiki)：

- [快速开始](https://github.com/wzklhk/mml-manager/wiki/Getting-Started)
- [命令行转换：MML 转表格、JSON、SQL/SQLite](https://github.com/wzklhk/mml-manager/wiki/Command-Line-Conversion)
- [系统架构](https://github.com/wzklhk/mml-manager/wiki/Architecture)
- [配置与部署](https://github.com/wzklhk/mml-manager/wiki/Configuration-and-Deployment)
- [HTTP API](https://github.com/wzklhk/mml-manager/wiki/HTTP-API)
- [MML 配置对比](https://github.com/wzklhk/mml-manager/wiki/MML-Comparison)
- [项目路线图](https://github.com/wzklhk/mml-manager/wiki/Roadmap)

> README 仅保留项目摘要；具体实现细节请更新到 Wiki。
