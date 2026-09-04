# -*- coding: utf-8 -*-
"""
业务逻辑层 (Service)
处理 MML 导入/导出/CRUD 的业务规则。
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from converters.mml_to_sql import parse_any_command
from dao import mml_dao
from utils.mml import format_mml_command


KEY_FIELD_CANDIDATES = (
    "ID", "INDEX", "SEQ", "SEQUENCE", "NAME", "MOID", "DN", "OBJECTID",
)


def _read_mml_text(file_path: str) -> str:
    """读取常见网元导出编码，UTF-8 失败时兼容 GB18030。"""
    with open(file_path, "rb") as f:
        content = f.read()
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("文件编码无法识别，请使用 UTF-8 或 GB18030 编码")


def _parse_mml_text(text: str) -> Dict[str, List[Dict]]:
    """解析文本，并支持一条命令跨多行书写。"""
    tables: Dict[str, List[Dict]] = {}
    buffer = ""
    commands = []
    quoted = False
    index = 0
    # 分号只有在引号外才表示命令结束；MML 用两个双引号表示引号转义。
    while index < len(text):
        char = text[index]
        if char == '"':
            if quoted and index + 1 < len(text) and text[index + 1] == '"':
                buffer += '""'
                index += 2
                continue
            quoted = not quoted
        buffer += char
        if char == ";" and not quoted:
            commands.append(buffer)
            buffer = ""
        index += 1
    if buffer.strip():
        commands.append(buffer)

    for raw_command in commands:
        command_lines = []
        for raw_line in raw_command.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("--") or line.startswith("//") or line.startswith("ENTER"):
                continue
            command_lines.append(line)
        parsed = parse_any_command(" ".join(command_lines))
        if parsed:
            tables.setdefault(parsed["table"], []).append(parsed)
    return tables


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
    baseline = _parse_mml_text(_read_mml_text(baseline_path))
    target = _parse_mml_text(_read_mml_text(target_path))
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
    """
    导入 MML 文件。

    扫描文件 → 收集所有表和参数 → 动态建表 → 插入数据。

    Args:
        file_path: 临时 MML 文件路径

    Returns:
        {message, tables, total_count}
    """
    tables_data = {}  # table_name -> {columns: set, rows: [{values, cmd_type}]}
    total_count = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("--"):
                continue
            config = parse_any_command(line)
            if config:
                table_name = config["table"]
                if table_name not in tables_data:
                    tables_data[table_name] = {"columns": set(), "rows": []}
                tables_data[table_name]["columns"].update(config["values"].keys())
                tables_data[table_name]["rows"].append(config)
                total_count += 1

    if total_count == 0:
        return {"error": "未找到有效的MML命令"}

    imported_count = 0
    table_list = []

    for table_name, data in tables_data.items():
        columns = sorted(data["columns"])

        # 建表
        mml_dao.create_table_if_not_exists(table_name, columns)
        # 确保列完整（已有表可能有缺失列）
        mml_dao.ensure_columns(table_name, columns)

        # 插入数据
        for config in data["rows"]:
            try:
                mml_dao.insert_row(table_name, config["values"])
                imported_count += 1
            except Exception as e:
                # 列缺失导致插入失败 → 补列重试
                mml_dao.ensure_columns(table_name, list(config["values"].keys()))
                try:
                    mml_dao.insert_row(table_name, config["values"])
                    imported_count += 1
                except Exception as e2:
                    print(f"[ERROR] 插入{table_name}失败: {e2}")

        # 更新元数据
        mml_dao.upsert_meta(table_name, columns)
        table_list.append(table_name)

    return {
        "message": f"成功导入 {imported_count} 条配置",
        "tables": table_list,
        "total_count": imported_count,
    }


def get_tables_summary() -> List[Dict]:
    """获取所有 MML 表及其统计"""
    metas = mml_dao.get_all_meta_tables()
    result = []
    for m in metas:
        try:
            count = mml_dao.count_rows(m["table_name"])
        except Exception:
            count = 0
        result.append(
            {
                "table_name": m["table_name"],
                "columns": json.loads(m["columns_json"]),
                "count": count,
                "created_at": m["created_at"],
            }
        )
    return result


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

    meta = mml_dao.get_table_meta(table_name)
    if not meta:
        raise ValueError(f"表 {table_name} 不存在")

    columns = json.loads(meta["columns_json"])
    if not sort_by:
        # 默认按网元对象标识排序，避免导入顺序不同导致页面与导出结果难以核对。
        sort_by = next((field for field in KEY_FIELD_CANDIDATES if field in columns), None)
    rows, total = mml_dao.query_rows(table_name, columns, page, page_size, sort_by, sort_order)

    configs = []
    for r in rows:
        configs.append(
            {
                "id": r["id"],
                "table_name": table_name,
                "cmd_type": "SET",
                "config_data": r["config_data"],
                "created_at": meta.get("created_at", ""),
                "updated_at": meta.get("updated_at", ""),
            }
        )

    total_pages = max(1, (total + page_size - 1) // page_size)
    return {
        "configs": configs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def get_config(table_name: str, config_id: int) -> Optional[Dict]:
    """获取单条配置"""
    meta = mml_dao.get_table_meta(table_name)
    if not meta:
        raise ValueError(f"表 {table_name} 不存在")

    columns = json.loads(meta["columns_json"])
    row = mml_dao.query_row(table_name, config_id, columns)
    if not row:
        return None

    return {
        "id": row["id"],
        "table_name": table_name,
        "cmd_type": "SET",
        "config_data": row["config_data"],
        "created_at": meta.get("created_at", ""),
        "updated_at": meta.get("updated_at", ""),
    }


def add_config(table_name: str, config_data: Dict) -> int:
    """新增配置行，返回新行 id"""
    meta = mml_dao.get_table_meta(table_name)
    if not meta:
        raise ValueError(f"表 {table_name} 不存在，请先导入MML文件")

    # 检查是否有新列
    existing_columns = set(json.loads(meta["columns_json"]))
    new_columns = [c for c in config_data.keys() if c not in existing_columns]
    if new_columns:
        all_columns = sorted(existing_columns | set(new_columns))
        mml_dao.ensure_columns(table_name, new_columns)
        mml_dao.upsert_meta(table_name, all_columns)

    return mml_dao.insert_row(table_name, config_data)


def update_config(table_name: str, config_id: int, config_data: Dict) -> bool:
    """更新配置行"""
    meta = mml_dao.get_table_meta(table_name)
    if not meta:
        raise ValueError(f"表 {table_name} 不存在")

    # 检查新列
    existing_columns = set(json.loads(meta["columns_json"]))
    new_columns = [c for c in config_data.keys() if c not in existing_columns]
    if new_columns:
        all_columns = sorted(existing_columns | set(new_columns))
        mml_dao.ensure_columns(table_name, new_columns)
        mml_dao.upsert_meta(table_name, all_columns)

    return mml_dao.update_row(table_name, config_id, config_data)


def delete_config(table_name: str, config_id: int) -> bool:
    """删除配置行"""
    meta = mml_dao.get_table_meta(table_name)
    if not meta:
        raise ValueError(f"表 {table_name} 不存在")
    return mml_dao.delete_row(table_name, config_id)


def batch_delete_configs(table_name: str, ids: List[int]) -> int:
    """批量删除配置行，返回删除数量"""
    meta = mml_dao.get_table_meta(table_name)
    if not meta:
        raise ValueError(f"表 {table_name} 不存在")
    return mml_dao.delete_rows(table_name, ids)


def export_selected_rows(table_name: str, ids: List[int]) -> Dict:
    """导出选中的行"""
    meta = mml_dao.get_table_meta(table_name)
    if not meta:
        raise ValueError(f"表 {table_name} 不存在")

    columns = json.loads(meta["columns_json"])
    rows = mml_dao.query_rows_by_ids(table_name, ids, columns)
    if not rows:
        raise ValueError("没有可导出的数据")

    lines = []
    lines.append(f"-- 由MML Manager导出（选中行）\n")
    lines.append(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    for row in rows:
        line = format_mml_command("SET", table_name, row)
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
    if table_name:
        metas = [mml_dao.get_table_meta(table_name)] if mml_dao.get_table_meta(table_name) else []
        if not metas:
            raise ValueError(f"表 {table_name} 不存在")
    else:
        metas = mml_dao.get_all_meta_tables()

    if not metas:
        raise ValueError("没有可导出的配置")

    lines = []
    lines.append(f"-- 由MML Manager导出\n")
    lines.append(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    for meta in metas:
        tname = meta["table_name"]
        columns = json.loads(meta["columns_json"])
        sort_field = next((field for field in KEY_FIELD_CANDIDATES if field in columns), None)
        rows = mml_dao.query_all_rows(tname, columns, sort_field)
        if not rows:
            continue

        lines.append(f"-- ===== {tname} =====\n")
        for row in rows:
            line = format_mml_command("SET", tname, row)
            lines.append(line + "\n")
        lines.append("\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return {
        "content": "".join(lines),
        "filename": f"export_{timestamp}.mml",
    }
