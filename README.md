# MML Manager

面向核心网网元配置运维的本地 B/S 工具，用于整理、检索、转换和对比复杂的 MML 配置。

## 功能摘要

- 转换器与 CLI：MML 与 Excel、CSV、SQL、JSON 双向转换
- 配置表查询、排序、分页、编辑和导出
- 基线与现网 MML 的新增、删除、修改及字段级对比
- 双文件对比支持 UTF-8、GB18030 和跨行 MML；Web 导入当前按 UTF-8 逐行读取
- Vue 3 + Element Plus 界面，支持中英文及明暗主题

## 当前进展（2026-09-09）

当前 `main` 基于 Flask + SQLite，已具备配置维护与双文件差异分析能力。FastAPI、TXT 导入及内存多配置切换已在 `codex/fastapi-backend` 分支实现，尚未合入本次核查的主分支。

近期优先修复依赖安装与开发启动问题、统一解析行为，再验证迁移分支。配置版本管理、复合主键、关联检查及变更回退仍待完成；已知问题、验证记录及计划见[项目进展](https://github.com/wzklhk/mml-manager/wiki/Project-Status)和[路线图](https://github.com/wzklhk/mml-manager/wiki/Roadmap)。

## 快速启动

```bash
./run.sh
```

首次安装前请先查看[启动限制与临时处理](https://github.com/wzklhk/mml-manager/wiki/Getting-Started)：当前依赖文件含无效的 `pandas>=` 声明。

Windows PowerShell 使用 `.\run.ps1`。启动后访问 `http://localhost:5000`。

## 文档

完整的使用、架构、接口和实现文档统一维护在 [MML Manager Wiki](https://github.com/wzklhk/mml-manager/wiki)：

- [快速开始](https://github.com/wzklhk/mml-manager/wiki/Getting-Started)
- [系统架构](https://github.com/wzklhk/mml-manager/wiki/Architecture)
- [配置与部署](https://github.com/wzklhk/mml-manager/wiki/Configuration-and-Deployment)
- [HTTP API](https://github.com/wzklhk/mml-manager/wiki/HTTP-API)
- [MML 配置对比](https://github.com/wzklhk/mml-manager/wiki/MML-Comparison)
- [项目路线图](https://github.com/wzklhk/mml-manager/wiki/Roadmap)

> README 仅保留项目摘要；具体实现细节请更新到 Wiki。
