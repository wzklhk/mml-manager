#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MML配置管理Web服务 - Flask入口

两种模式：
  开发模式：前端 npm run serve (port 8080)，后端 Flask (port 5000)，vue proxy 处理跨域
  部署模式：前端 build → static/，Flask 统一提供前端静态文件 + API，无跨域问题
"""

import sys
import os

# 确保当前目录在路径中（方便导入同层模块）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from config import load_config
from dao.mml_dao import init_db
from controller.mml_controller import api

# 静态文件目录（前端 build 产物）
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
CORS(app)

# 注册 API Blueprint
app.register_blueprint(api)


# ── SPA 路由：所有非 API 路径都返回 index.html ──
@app.route("/")
def serve_index():
    """首页 → static/index.html"""
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/<path:path>")
def serve_static_or_fallback(path):
    """
    提供静态文件或 SPA 回退。
    优先返回 static/ 下的物理文件，否则返回 index.html 让 Vue Router 处理。
    """
    file_path = os.path.join(STATIC_DIR, path)

    # 检查物理文件是否存在
    if os.path.isfile(file_path):
        # Flask 内置的 static 路由会处理 /static/ 前缀，但我们手动处理非 /static/ 的路径
        return send_from_directory(STATIC_DIR, path)

    # SPA 回退：非 API 路径都返回 index.html
    if not path.startswith("api/"):
        return send_from_directory(STATIC_DIR, "index.html")

    # API 路径不应走到这里 — 由 blueprint 处理
    return {"error": "Not found"}, 404


# ── 启动 ──
if __name__ == "__main__":
    settings = load_config()

    # 初始化数据库
    init_db(settings["database"]["path"])

    host = settings["server"]["host"]
    port = settings["server"]["port"]
    debug = settings["server"]["debug"]

    print("\n" + "=" * 60)
    print("MML配置管理系统 启动中...")
    print("=" * 60)
    print(f"API地址:     http://{host}:{port}/api")
    print(f"前端页面:    http://{host}:{port}/")
    print(f"数据库:      {settings['database']['path']}")
    print(f"静态文件:    {STATIC_DIR}")
    print(f"模式:        {'开发(debug)' if debug else '生产'}")
    print(f"架构:        Controller → Service → DAO")
    print("=" * 60 + "\n")

    app.run(host=host, port=port, debug=debug)
