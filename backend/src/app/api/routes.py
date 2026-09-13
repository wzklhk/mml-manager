# -*- coding: utf-8 -*-
"""FastAPI 路由定义与 HTTP 请求/响应处理。"""

import json
import os
from datetime import datetime
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, File, Form, Query, UploadFile
from fastapi.responses import JSONResponse, Response
from starlette.concurrency import run_in_threadpool

from ..services import mml as mml_service

api = APIRouter(prefix="/api")
MAX_COMPARE_FILE_SIZE = 20 * 1024 * 1024


def _error(message: str, status_code: int) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status_code)


def _is_import_file(file: UploadFile | None) -> bool:
    return bool(file and file.filename and file.filename.lower().endswith((".mml", ".txt")))


async def _read_upload(file: UploadFile, max_size: int | None = None) -> bytes:
    """Read an upload into process memory, enforcing a limit while streaming."""
    content = bytearray()
    size = 0
    try:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if max_size is not None and size > max_size:
                raise ValueError("单个文件不能超过 20 MB")
            content.extend(chunk)
        return bytes(content)
    finally:
        await file.close()


@api.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@api.post("/import-mml")
async def import_mml(
    file: UploadFile | None = File(default=None),
    network_element: str | None = Form(default=None),
):
    if file is None:
        return _error("未上传文件", 400)
    if not file.filename:
        return _error("文件名为空", 400)
    if not _is_import_file(file):
        return _error("只支持 .mml 或 .txt 格式文件", 400)
    try:
        result = await run_in_threadpool(mml_service.import_mml_stream, file.file, file.filename, network_element)
        return JSONResponse(result, status_code=400) if "error" in result else result
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"导入失败: {exc}", 500)
    finally:
        await file.close()


@api.post("/compare-mml")
async def compare_mml(
    baseline: UploadFile | None = File(default=None),
    target: UploadFile | None = File(default=None),
):
    if not _is_import_file(baseline) or not _is_import_file(target):
        return _error("请上传两份 .mml 或 .txt 文件", 400)
    try:
        baseline_text = mml_service.decode_mml_bytes(await _read_upload(baseline, MAX_COMPARE_FILE_SIZE))
        target_text = mml_service.decode_mml_bytes(await _read_upload(target, MAX_COMPARE_FILE_SIZE))
        return mml_service.compare_mml_texts(baseline_text, target_text)
    except ValueError as exc:
        return _error(str(exc), 413 if "20 MB" in str(exc) else 400)
    except Exception as exc:
        return _error(f"对比失败: {exc}", 500)


@api.get("/tables")
def get_tables():
    try:
        return {"tables": mml_service.get_tables_summary()}
    except Exception as exc:
        return _error(str(exc), 500)


@api.get("/snapshots")
def get_snapshots():
    return mml_service.get_snapshots()


@api.get("/cache/stats")
def get_cache_stats():
    """Expose bounded-cache utilization for local diagnostics."""
    return mml_service.store.cache_stats()


@api.post("/snapshots/{snapshot_id}/activate")
def activate_snapshot(snapshot_id: str):
    try:
        return {"snapshot": mml_service.activate_snapshot(snapshot_id)}
    except ValueError as exc:
        return _error(str(exc), 404)


@api.delete("/snapshots/{snapshot_id}")
@api.post("/snapshots/{snapshot_id}/delete")
def delete_snapshot(snapshot_id: str):
    try:
        deleted = mml_service.delete_snapshot(snapshot_id)
        return {
            "message": "配置删除成功",
            "deleted": deleted,
            "active_id": deleted["active_id"],
        }
    except ValueError as exc:
        return _error(str(exc), 404)


@api.get("/configs")
def get_configs(
    table_name: str = "",
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    sort_by: str | None = None,
    sort_order: str = "asc",
    filters: str | None = None,
):
    try:
        column_filters = json.loads(filters) if filters else {}
        if not isinstance(column_filters, dict):
            return _error("筛选条件格式无效", 400)
        table_name = table_name.strip()
        if table_name:
            return mml_service.get_configs(table_name, page, page_size, sort_by, sort_order, column_filters)
        summary = {
            table["table_name"]: {"count": table["count"], "columns": table["columns"]}
            for table in mml_service.get_tables_summary()
        }
        return {
            "tables_summary": summary,
            "configs": [],
            "total": 0,
            "page": 1,
            "page_size": page_size,
            "total_pages": 1,
        }
    except json.JSONDecodeError:
        return _error("筛选条件格式无效", 400)
    except ValueError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        return _error(f"查询失败: {exc}", 500)


@api.post("/configs", status_code=201)
def add_config(data: dict[str, Any] | None = None):
    if not data:
        return _error("请求数据为空", 400)
    table_name, config_data = data.get("table_name", ""), data.get("config_data", {})
    if not table_name or not config_data:
        return _error("需要 table_name 和 config_data", 400)
    try:
        return JSONResponse(
            {"message": "新增成功", "id": mml_service.add_config(table_name, config_data)}, status_code=201
        )
    except ValueError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        return _error(f"新增失败: {exc}", 500)


@api.post("/configs/batch-delete")
def batch_delete_configs(data: dict[str, Any] | None = None):
    data = data or {}
    table_name, ids = data.get("table_name", ""), data.get("ids", [])
    if not table_name or not ids:
        return _error("需要 table_name 和 ids", 400)
    try:
        deleted = mml_service.batch_delete_configs(table_name, ids)
        return {"message": f"成功删除 {deleted} 条配置", "deleted": deleted}
    except ValueError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        return _error(f"批量删除失败: {exc}", 500)


@api.get("/configs/{config_id}")
def get_config(config_id: int, table_name: str = ""):
    if not table_name:
        return _error("需要指定 table_name 参数", 400)
    try:
        config = mml_service.get_config(table_name, config_id)
        return config if config else _error("配置不存在", 404)
    except ValueError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        return _error(str(exc), 500)


@api.put("/configs/{config_id}")
def update_config(config_id: int, data: dict[str, Any] | None = None):
    if not data:
        return _error("请求数据为空", 400)
    table_name = data.get("table_name", "")
    if not table_name:
        return _error("需要指定 table_name", 400)
    try:
        success = mml_service.update_config(table_name, config_id, data.get("config_data", {}))
        return {"message": "配置更新成功"} if success else _error("配置不存在", 404)
    except ValueError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        return _error(f"更新失败: {exc}", 500)


@api.delete("/configs/{config_id}")
def delete_config(config_id: int, table_name: str = ""):
    if not table_name:
        return _error("需要指定 table_name 参数", 400)
    try:
        success = mml_service.delete_config(table_name, config_id)
        return {"message": "配置删除成功"} if success else _error("配置不存在", 404)
    except ValueError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        return _error(f"删除失败: {exc}", 500)


@api.post("/export-mml")
def export_mml(data: dict[str, Any] | None = None):
    data = data or {}
    table_name, ids = data.get("table_name"), data.get("ids")
    try:
        return mml_service.export_selected_rows(table_name, ids) if ids else mml_service.export_mml(table_name)
    except ValueError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        return _error(f"导出失败: {exc}", 500)


@api.post("/export")
def export_configurations(data: dict[str, Any] | None = None):
    data = data or {}
    try:
        result = mml_service.export_configurations(
            data.get("format", ""),
            data.get("table_name"),
            data["ids"] if "ids" in data else None,
        )
        filename = result["filename"]
        ascii_fallback = "export" + os.path.splitext(filename)[1]
        disposition = f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{quote(filename)}"
        return Response(
            content=result["content"],
            media_type=result["media_type"],
            headers={
                "Content-Disposition": disposition,
                "X-Export-Count": str(result["count"]),
                "Access-Control-Expose-Headers": "Content-Disposition, X-Export-Count",
            },
        )
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"导出失败: {exc}", 500)
