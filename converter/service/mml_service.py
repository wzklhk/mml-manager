# -*- coding: utf-8 -*-
"""
业务逻辑层 (Service)
处理 MML 导入/导出/CRUD 的业务规则。
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from mml_parser import parse_mml_text
from service.memory_store import store
from utils.mml import format_mml_command


KEY_FIELD_CANDIDATES = (
    "ID", "INDEX", "SEQ", "SEQUENCE", "NAME", "MOID", "DN", "OBJECTID",
)


def decode_mml_bytes(content: bytes) -> str:
    """Decode common network-element export encodings."""
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("文件编码无法识别，请使用 UTF-8 或 GB18030 编码")


def _read_mml_text(file_path: str) -> str:
    with open(file_path, "rb") as handle:
        return decode_mml_bytes(handle.read())


def _parse_mml_text(text: str) -> Dict[str, List[Dict]]:
    return parse_mml_text(text)


def _choose_key_fields(before: List[Dict], after: List[Dict]) -> List[str]:
    """选择两侧均存在且能唯一标识记录的字段。"""
    rows = [item["values"] for item in before + after]
    if not rows:
        return []
    common = set(rows[0])
    for row in rows[1:]:
        common.intersection_update(row)
    candidates = [field for field in KEY_FIELD_CANDIDATES if field in common]
    candidates.extend(sorted(field for field in common if field.endswith("_ID") and field not in candidates))
    for field in candidates:
        before_keys = [str(item["values"].get(field, "")) for item in before]
        after_keys = [str(item["values"].get(field, "")) for item in after]
        if all(before_keys + after_keys) and len(before_keys) == len(set(before_keys)) and len(after_keys) == len(set(after_keys)):
            return [field]
    return []


def _record_key(values: Dict, fields: List[str]) -> str:
    return " | ".join(f"{field}={values.get(field, '')}" for field in fields)


def compare_mml_files(baseline_path: str, target_path: str) -> Dict:
    """对比两份 MML 配置，返回表级和字段级差异，不写入数据库。"""
    return compare_mml_texts(_read_mml_text(baseline_path), _read_mml_text(target_path))


def compare_mml_texts(baseline_text: str, target_text: str) -> Dict:
    """Compare two already-loaded MML texts entirely in memory."""
    baseline = _parse_mml_text(baseline_text)
    target = _parse_mml_text(target_text)
    if not baseline and not target:
        raise ValueError("两份文件中都没有找到有效的 SET/ADD 命令")

    table_results = []
    totals = {"added": 0, "removed": 0, "modified": 0, "unchanged": 0}
    for table_name in sorted(set(baseline) | set(target)):
        before = baseline.get(table_name, [])
        after = target.get(table_name, [])
        key_fields = _choose_key_fields(before, after)
        warning = None
        if key_fields:
            before_map = {_record_key(item["values"], key_fields): item["values"] for item in before}
            after_map = {_record_key(item["values"], key_fields): item["values"] for item in after}
        else:
            # 无稳定主键时仍可准确识别完全相同、新增和删除，避免错误地配对为“修改”。
            warning = "未发现唯一标识字段，无法判定字段级修改；差异按完整配置行识别"
            def canonical(item):
                return json.dumps(item["values"], ensure_ascii=False, sort_keys=True)
            before_map = {canonical(item): item["values"] for item in before}
            after_map = {canonical(item): item["values"] for item in after}

        diffs = []
        for key in sorted(set(before_map) | set(after_map)):
            old = before_map.get(key)
            new = after_map.get(key)
            if old is None:
                status, changes = "added", []
            elif new is None:
                status, changes = "removed", []
            elif old != new:
                status = "modified"
                changes = [
                    {"field": field, "before": old.get(field), "after": new.get(field)}
                    for field in sorted(set(old) | set(new))
                    if old.get(field) != new.get(field)
                ]
            else:
                status, changes = "unchanged", []
            totals[status] += 1
            if status != "unchanged":
                diffs.append({"key": key, "status": status, "before": old, "after": new, "changes": changes})

        table_results.append({
            "table_name": table_name,
            "key_fields": key_fields,
            "baseline_count": len(before),
            "target_count": len(after),
            "warning": warning,
            "diffs": diffs,
            "summary": {
                status: sum(1 for diff in diffs if diff["status"] == status)
                for status in ("added", "removed", "modified")
            },
        })
    return {"summary": totals, "tables": table_results}


def import_mml_file(file_path: str) -> Dict:
    """Parse a file into the active in-memory snapshot."""
    return import_mml_text(_read_mml_text(file_path), os.path.basename(file_path))


def import_mml_text(text: str, name: str = "未命名配置") -> Dict:
    """Parse text, add a named snapshot, and make it active."""
    tables = _parse_mml_text(text)
    total_count = sum(len(commands) for commands in tables.values())
    if not total_count:
        return {"error": "未找到有效的MML命令"}
    snapshot = store.add_snapshot(tables, name)
    return {
        "message": f"成功解析 {total_count} 条配置到内存",
        "tables": list(tables),
        "total_count": total_count,
        "snapshot": snapshot,
    }


def get_snapshots() -> Dict:
    snapshots, active_id = store.list_snapshots()
    return {"snapshots": snapshots, "active_id": active_id}


def activate_snapshot(snapshot_id: str) -> Dict:
    return store.activate(snapshot_id)


def get_tables_summary() -> List[Dict]:
    tables, loaded_at = store.snapshot()
    return [{"table_name": name, "columns": table["columns"], "count": len(table["rows"]),
             "created_at": loaded_at or ""}
            for name, table in sorted(tables.items(), key=lambda item: item[0].casefold())]


def get_configs(
    table_name: str, page: int = 1, page_size: int = 20, sort_by: str = None, sort_order: str = "asc"
) -> Dict:
    """
    分页获取配置列表。

    Returns:
        {configs, total, page, page_size, total_pages}
    """
    if not table_name:
        return {"configs": [], "total": 0, "page": 1, "page_size": page_size, "total_pages": 1}

    tables, loaded_at = store.snapshot()
    if table_name not in tables:
        raise ValueError(f"表 {table_name} 不存在")
    table = tables[table_name]
    columns = table["columns"]
    if not sort_by:
        # 默认按网元对象标识排序，避免导入顺序不同导致页面与导出结果难以核对。
        sort_by = next((field for field in KEY_FIELD_CANDIDATES if field in columns), None)
    rows = table["rows"]
    if sort_by in columns:
        def sort_value(row):
            value = row["values"].get(sort_by)
            try:
                return value is None, 0, float(value)
            except (TypeError, ValueError):
                return value is None, 1, str(value or "").casefold()

        rows.sort(key=sort_value,
                  reverse=sort_order.lower() == "desc")
    total = len(rows)
    start = max(0, (page - 1) * page_size)
    configs = [{"id": row["id"], "table_name": table_name, "cmd_type": row["cmd_type"],
                "config_data": {column: row["values"].get(column) for column in columns},
                "created_at": loaded_at or "", "updated_at": loaded_at or ""}
               for row in rows[start:start + page_size]]
    total_pages = max(1, (total + page_size - 1) // page_size)
    return {
        "configs": configs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def get_config(table_name: str, config_id: int) -> Optional[Dict]:
    tables, loaded_at = store.snapshot()
    if table_name not in tables:
        raise ValueError(f"表 {table_name} 不存在")
    table = tables[table_name]
    row = next((item for item in table["rows"] if item["id"] == config_id), None)
    return None if row is None else {"id": row["id"], "table_name": table_name,
        "cmd_type": row["cmd_type"], "config_data": row["values"],
        "created_at": loaded_at or "", "updated_at": loaded_at or ""}


def add_config(table_name: str, config_data: Dict) -> int:
    return store.add(table_name, config_data)


def update_config(table_name: str, config_id: int, config_data: Dict) -> bool:
    return store.update(table_name, config_id, config_data)


def delete_config(table_name: str, config_id: int) -> bool:
    return store.delete(table_name, [config_id]) > 0


def batch_delete_configs(table_name: str, ids: List[int]) -> int:
    return store.delete(table_name, ids)


def export_selected_rows(table_name: str, ids: List[int]) -> Dict:
    tables, _ = store.snapshot()
    if table_name not in tables:
        raise ValueError(f"表 {table_name} 不存在")
    wanted = set(ids)
    rows = [row for row in tables[table_name]["rows"] if row["id"] in wanted]
    if not rows:
        raise ValueError("没有可导出的数据")

    lines = []
    lines.append(f"-- 由MML Manager导出（选中行）\n")
    lines.append(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    for row in rows:
        line = format_mml_command(row["cmd_type"], table_name, row["values"])
        lines.append(line + "\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return {
        "content": "".join(lines),
        "filename": f"{table_name}_selected_{timestamp}.mml",
    }


def export_mml(table_name: Optional[str] = None) -> Dict:
    """
    导出为 MML 格式。

    Returns:
        {content, filename}
    """
    tables, _ = store.snapshot()
    if table_name:
        if table_name not in tables:
            raise ValueError(f"表 {table_name} 不存在")
        tables = {table_name: tables[table_name]}
    if not tables:
        raise ValueError("没有可导出的配置")

    lines = []
    lines.append(f"-- 由MML Manager导出\n")
    lines.append(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    for tname, table in tables.items():
        rows = table["rows"]
        if not rows:
            continue

        lines.append(f"-- ===== {tname} =====\n")
        for row in rows:
            line = format_mml_command(row["cmd_type"], tname, row["values"])
            lines.append(line + "\n")
        lines.append("\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return {
        "content": "".join(lines),
        "filename": f"export_{timestamp}.mml",
    }
