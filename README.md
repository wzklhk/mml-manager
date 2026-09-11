# MML Manager

面向核心网网元配置运维的本地 B/S 工具，用于整理、检索、转换和对比复杂的 MML 配置。

## 功能摘要

- MML 与 Excel、CSV、SQL、JSON 双向转换
- 配置表查询、排序、分页、编辑和导出
- 基线与现网 MML 的新增、删除、修改及字段级对比
- 完整解析 `ADD`/`SET`，兼容含空格命令名、单双引号值、UTF-8 与 GB18030
- 导入会创建可切换的进程内配置快照；查看、编辑、删除和导出均操作当前快照
- Web 配置管理暂未接入 SQLite：服务重启会清空快照，多 worker 之间也不共享数据

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

前端没有变化且已有 `converter/static` 构建产物时，可使用 `.\run.ps1 start` 或 `./run.sh start` 跳过打包；日常开发使用 `.\run.ps1 dev` 或 `./run.sh dev`，由 Vite 提供热更新，也不会生成生产包。

更多启动方式、环境配置和 API 地址见 Wiki 的[快速开始](https://github.com/wzklhk/mml-manager/wiki/Getting-Started)。

## 文档

完整的使用、架构、接口和实现文档统一维护在 [MML Manager Wiki](https://github.com/wzklhk/mml-manager/wiki)：

- [快速开始](https://github.com/wzklhk/mml-manager/wiki/Getting-Started)
- [系统架构](https://github.com/wzklhk/mml-manager/wiki/Architecture)
- [配置与部署](https://github.com/wzklhk/mml-manager/wiki/Configuration-and-Deployment)
- [HTTP API](https://github.com/wzklhk/mml-manager/wiki/HTTP-API)
- [MML 配置对比](https://github.com/wzklhk/mml-manager/wiki/MML-Comparison)
- [项目路线图](https://github.com/wzklhk/mml-manager/wiki/Roadmap)

> README 仅保留项目摘要；具体实现细节请更新到 Wiki。
