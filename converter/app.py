#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MML 配置管理 Web 服务的 FastAPI 入口。"""

import os
import sys
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import load_config
from controller.mml_controller import api
from dao.mml_dao import init_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = load_config()
    init_db(settings["database"]["path"])
    yield


app = FastAPI(title="MML Manager API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(api)
app.mount("/static", StaticFiles(directory=STATIC_DIR, check_dir=False), name="static")


@app.get("/")
def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index_path) if os.path.isfile(index_path) else JSONResponse(
        {"error": "前端尚未构建"}, status_code=404
    )


@app.get("/{path:path}")
def serve_static_or_fallback(path: str):
    file_path = os.path.abspath(os.path.join(STATIC_DIR, path))
    static_root = os.path.abspath(STATIC_DIR)
    if os.path.commonpath((static_root, file_path)) == static_root and os.path.isfile(file_path):
        return FileResponse(file_path)
    if not path.startswith("api/"):
        return serve_index()
    return JSONResponse({"error": "Not found"}, status_code=404)


if __name__ == "__main__":
    settings = load_config()
    uvicorn.run("app:app", host=settings["server"]["host"], port=settings["server"]["port"],
                reload=settings["server"]["debug"])
