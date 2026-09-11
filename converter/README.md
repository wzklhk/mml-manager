# MML Manager 后端

该 Python 包包含 MML Manager 的 FastAPI 应用、业务服务、存储实现、格式转换器和 CLI。

## 本地启动

```bash
python -m venv converter/.venv
converter/.venv/Scripts/pip install -e ".[test]"
converter/.venv/Scripts/python -m converter.main
```

完整说明请参阅项目 Wiki：

- [快速开始](https://github.com/wzklhk/mml-manager/wiki/Getting-Started)
- [系统架构](https://github.com/wzklhk/mml-manager/wiki/Architecture)
- [配置与部署](https://github.com/wzklhk/mml-manager/wiki/Configuration-and-Deployment)
- [HTTP API](https://github.com/wzklhk/mml-manager/wiki/HTTP-API)

具体实现细节不在本 README 重复维护。
