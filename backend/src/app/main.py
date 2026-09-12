#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MML 配置管理 Web 服务的 FastAPI 入口。"""

from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import api
from .core.config import load_config
from .repositories.sqlite import init_snapshot_schema

STATIC_DIR = Path(__file__).resolve().parent / "static"
frontend = APIRouter()


@asynccontextmanager
async def lifespan(_: FastAPI):
    load_config()
    init_snapshot_schema()
    yield


def create_app() -> FastAPI:
    """Build the ASGI application and register the current API routes."""
    application = FastAPI(title="MML Manager API", lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api)
    application.mount("/static", StaticFiles(directory=STATIC_DIR, check_dir=False), name="static")
    # The SPA catch-all must be registered last or it will return index.html for
    # JavaScript and CSS requests that belong to the static mount.
    application.include_router(frontend)
    return application


@frontend.get("/")
def serve_index():
    index_path = STATIC_DIR / "index.html"
    return (
        FileResponse(index_path) if index_path.is_file() else JSONResponse({"error": "前端尚未构建"}, status_code=404)
    )


@frontend.get("/{path:path}")
def serve_static_or_fallback(path: str):
    static_root = STATIC_DIR.resolve()
    file_path = (static_root / path).resolve()
    if file_path.is_relative_to(static_root) and file_path.is_file():
        return FileResponse(file_path)
    if not path.startswith("api/"):
        return serve_index()
    return JSONResponse({"error": "Not found"}, status_code=404)


app = create_app()


def run() -> None:
    """Run the development server using repository configuration."""
    settings = load_config()
    uvicorn.run(
        "app.main:app",
        host=settings["server"]["host"],
        port=settings["server"]["port"],
        reload=settings["server"]["debug"],
    )


if __name__ == "__main__":
    run()
