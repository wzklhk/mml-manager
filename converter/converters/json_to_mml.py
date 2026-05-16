# -*- coding: utf-8 -*-
"""JSON → MML 转换核心模块"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from utils.mml import format_mml_command, format_mml_value_simple


def escape_mml_value(value: Any) -> str:
    """转义 MML 值，处理特殊字符和引号"""
    if value is None:
        return ''
    s = str(value)
    if ',' in s or ';' in s or '=' in s or isinstance(value, str) and not s.replace('.', '', 1).isdigit():
        q = chr(34)
        s = s.replace(q, q + q)
        return f'{q}{s}{q}'
    return s


def convert_json_to_mml(
    json_file: str, output_file: str,
    encoding: str = 'utf-8',
) -> Dict[str, Any]:
    """转换 JSON 文件为 MML。

    JSON 格式:
    {
        "table_name": [
            {"cmd_type": "SET", "values": {"ID": "1", "NAME": "xxx"}},
            ...
        ]
    }

    Returns:
        统计信息: {total, tables}
    """
    with open(json_file, 'r', encoding=encoding) as f:
        data = json.load(f)

    # 支持两种格式
    if 'configs' in data:
        configs = data['configs']
    elif 'tables' in data:
        configs = data['tables']
    else:
        configs = data

    total = 0
    lines = []
    lines.append(f"-- 由 json2mml.py 生成\n")
    lines.append(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    tables_found = []

    for table_name, records in configs.items():
        if not records:
            continue
        tables_found.append(table_name)
        lines.append(f"-- ===== {table_name} =====\n")

        for record in records:
            cmd_type = record.get('cmd_type', 'SET')
            values = record.get('values', record.get('config_data', {}))
            mml_parts = []
            for key, val in values.items():
                mml_parts.append(f'{key}={escape_mml_value(val)}')
            if mml_parts:
                lines.append(f"{cmd_type} {table_name}:{','.join(mml_parts)};\n")
                total += 1

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return {'total': total, 'tables': tables_found}
