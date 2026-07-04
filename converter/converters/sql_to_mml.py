# -*- coding: utf-8 -*-
"""SQL → MML 转换核心模块"""

import re
import os
from typing import Dict, List, Optional
from datetime import datetime

from converters.mml_to_sql import parse_key_value_pairs
from utils.io_handler import write_mml_file, print_statistics
from utils.table import MmlDataSet, MmlConfig, sanitize_table_name
from utils.mml import quote_mml_value


def parse_insert_statements(sql_text: str) -> List[Dict]:
    """从 SQL 文本中解析 INSERT 语句。"""
    results = []
    current_table = None
    current_columns = None
    i = 0
    lines = sql_text.split("\n")

    while i < len(lines):
        line = lines[i].strip()

        # 多行 INSERT ... VALUES
        insert_match = re.match(r"INSERT\s+(?:INTO\s+)?(\w+)\s*\((.+?)\)\s*VALUES\s*\(", line, re.IGNORECASE)
        if insert_match:
            table = insert_match.group(1)
            cols = [c.strip().strip('`"[]') for c in insert_match.group(2).split(",")]
            current_table = table
            current_columns = cols

            # 收集值 — 如果当前行已有分号则跳过行收集
            values_block = "(" + line[insert_match.end() :]
            if ";" not in line:
                i += 1
                while i < len(lines):
                    values_block += "\n" + lines[i].strip()
                    if ";" in lines[i]:
                        break
                    i += 1

            value_sets = _parse_value_tuples(values_block)
            for vs in value_sets:
                kv = {}
                for idx, col in enumerate(cols):
                    kv[col] = vs[idx] if idx < len(vs) else ""
                results.append({"table": current_table, "values": kv})
            current_table = None
            current_columns = None
            i += 1
            continue
        i += 1

    return results


def _parse_value_tuples(values_block: str) -> List[List[str]]:
    """解析 VALUES 后的元组列表"""
    block = values_block
    if ";" in block:
        block = block[: block.index(";")]

    tuples = []
    depth = 0
    current = ""
    for ch in block:
        if ch == "(":
            if depth > 0:
                current += ch
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                if current.strip():
                    tuples.append(_parse_single_value_tuple(current.strip()))
                current = ""
            else:
                current += ch
        elif ch == "," and depth == 0:
            # 元组之间的逗号 (e.g. (1,2),(3,4))
            if current.strip():
                tuples.append(_parse_single_value_tuple(current.strip()))
            current = ""
        else:
            if depth >= 1:
                current += ch

    return tuples


def _parse_single_value_tuple(text: str) -> List[str]:
    """解析单行值，按逗号分隔"""
    values = []
    current = ""
    in_quote = False
    quote_char = None
    for ch in text:
        if ch in ("'", '"'):
            if not in_quote:
                in_quote = True
                quote_char = ch
            elif ch == quote_char:
                in_quote = False
                quote_char = None
            else:
                current += ch
        elif ch == "," and not in_quote:
            values.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        values.append(current.strip())
    return values


def parse_select_result(sql_text: str) -> List[Dict]:
    """从 SELECT 结果表格文本中解析数据"""
    results = []
    lines = sql_text.strip().split("\n")
    if not lines:
        return results

    # 第一行是表头
    headers = [h.strip() for h in lines[0].split("|") if h.strip()]
    if not headers:
        return results

    for line in lines[2:]:
        line = line.strip()
        if not line or line.startswith("+") or line.startswith("---"):
            continue
        cells = _parse_table_row(line)
        if len(cells) >= len(headers):
            kv = {}
            for idx, h in enumerate(headers):
                kv[h] = cells[idx].strip()
            results.append({"table": "UNKNOWN", "values": kv})

    return results


def _parse_table_row(line: str) -> List[str]:
    """解析表格行"""
    return [cell.strip() for cell in line.split("|") if cell.strip()]


def sql_data_to_dataset(
    data: List[Dict],
    cmd_type: str = "SET",
    default_table: str = None,
) -> MmlDataSet:
    """将解析后的 SQL 数据转为 MmlDataSet"""
    dataset = MmlDataSet()
    for item in data:
        table_name = item.get("table", default_table or "TABLE")
        values = {}
        for k, v in item.get("values", {}).items():
            key = k.strip().strip('`"[]')
            val = v.strip().strip("'\"") if v else ""
            values[key] = quote_mml_value(val)

        dataset.add(MmlConfig(cmd_type=cmd_type, table=table_name, values=values))

    return dataset


def convert_sql_file(
    input_path: str,
    output_path: str,
    cmd_type: str = "SET",
    encoding: str = "utf-8",
    input_format: str = "auto",
    table_name: str = None,
) -> MmlDataSet:
    """转换 SQL 文件为 MML"""
    with open(input_path, "r", encoding=encoding) as f:
        sql_text = f.read()

    if input_format == "auto":
        if re.search(r"INSERT\s+INTO", sql_text, re.IGNORECASE):
            input_format = "insert"
        else:
            input_format = "select"

    if input_format == "insert":
        data = parse_insert_statements(sql_text)
    else:
        data = parse_select_result(sql_text)

    if table_name:
        for item in data:
            item["table"] = table_name

    dataset = sql_data_to_dataset(data, cmd_type)

    if output_path:
        write_mml_file(
            output_path, dataset, source_desc=f"sql2mml.py 从 {os.path.basename(input_path)}", cmd_type=cmd_type
        )

    return dataset
