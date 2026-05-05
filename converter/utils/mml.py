# -*- coding: utf-8 -*-
"""
公共MML格式化函数模块

提供MML命令格式化和值转义的通用功能。
所有与 MML 语法输出相关的函数集中于此。
"""
import re
from typing import Any


def quote_mml_value(value: Any) -> str:
    """
    将值格式化为MML值。
    - None → 空字符串
    - 浮点整数 (如 201.0) → 整数格式 '201'
    - 字符串含空格/逗号/分号/双引号 → 双引号括起并转义内部双引号

    Args:
        value: 待格式化的值

    Returns:
        格式化后的MML值字符串
    """
    if value is None:
        return ''
    if isinstance(value, float):
        if value == int(value):
            return str(int(value))
        return str(value)
    value = str(value).strip()
    if not value:
        return ''
    if re.search(r'[\s,;"]', value):
        escaped = value.replace('"', '""')
        return f'"{escaped}"'
    return value


def format_mml_command(cmd_type: str, table: str, data: dict) -> str:
    """
    格式化MML命令。

    Args:
        cmd_type: 命令类型 (SET/ADD)
        table: 表名
        data: 键值对字典

    Returns:
        格式化的MML命令字符串，如: SET LTE_CELL:ID=1,NAME="Cell_A";
    """
    if not data:
        return ''
    kv_pairs = []
    for key, val in data.items():
        kv_pairs.append(f"{key}={quote_mml_value(val)}")
    return f"{cmd_type} {table}:{','.join(kv_pairs)};"


def format_mml_value_simple(value: Any) -> str:
    """
    简化版MML值格式化（用于CSV转换）。
    - None/NaN → 空字符串
    - 数字 → 直接转为字符串
    - 字符串 → 如果包含逗号、空格、等号或引号，加双引号

    Args:
        value: 待格式化的值

    Returns:
        格式化后的MML值字符串
    """
    if value is None:
        return ""
    val_str = str(value).strip()
    if not val_str:
        return ""
    if any(c in val_str for c in [',', ' ', '=', '"', "'"]):
        val_str = val_str.replace('"', '\\"')
        return f'"{val_str}"'
    return val_str
