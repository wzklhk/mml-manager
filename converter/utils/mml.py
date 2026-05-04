# -*- coding: utf-8 -*-
"""
公共MML格式化函数模块
提供MML命令格式化的通用功能
"""
import re
from typing import Any


def quote_mml_value(value: Any) -> str:
    """
    将值格式化为MML值
    - None -> 'NULL'
    - 数字 -> 直接转为字符串
    - 字符串 -> 如果包含空格、逗号、分号或双引号，加双引号并转义
    
    Args:
        value: 待格式化的值
        
    Returns:
        格式化后的MML值字符串
    """
    if value is None:
        return 'NULL'
    if not isinstance(value, str):
        return str(value)
    # 如果值包含空格、逗号、分号或双引号，需要加引号
    if re.search(r'[\s,;"]', value):
        escaped = value.replace('"', '""')
        return f'"{escaped}"'
    return value


def escape_mml_value(value: Any) -> str:
    """
    转义MML值的别名函数
    """
    return quote_mml_value(value)


def format_mml_command(cmd_type: str, table: str, data: dict) -> str:
    """
    格式化MML命令
    
    Args:
        cmd_type: 命令类型 (SET/ADD)
        table: 表名
        data: 键值对字典
        
    Returns:
        格式化的MML命令字符串
    """
    kv_pairs = []
    for key, val in data.items():
        kv_pairs.append(f"{key}={quote_mml_value(val)}")
    return f"{cmd_type} {table}:{','.join(kv_pairs)};"


def format_mml_value_simple(value: Any) -> str:
    """
    简化版MML值格式化（用于CSV转换）
    - None/NaN -> 空字符串
    - 数字 -> 直接转为字符串
    - 字符串 -> 如果包含逗号、空格、等号或引号，加双引号
    
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
    # 检查是否需要引号
    if any(c in val_str for c in [',', ' ', '=', '"', "'"]):
        val_str = val_str.replace('"', '\\"')
        return f'"{val_str}"'
    return val_str
