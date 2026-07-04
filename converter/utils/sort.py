# -*- coding: utf-8 -*-
"""
公共排序函数模块
提供MML记录排序的通用功能
"""

from typing import List, Dict, Any


def try_parse_int(value: Any) -> int | None:
    """
    尝试将值解析为整数，失败返回None

    Args:
        value: 待解析的值

    Returns:
        整数或None
    """
    if value is None or value == "":
        return None
    value = str(value).strip()
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def sort_records(records: List[Dict[str, Any]], id_fields: List[str] = None) -> List[Dict[str, Any]]:
    """
    对记录列表进行升序排序

    优先按 ID 字段（如果存在），否则按字典的第一个键值对排序。
    智能识别数字：如果值全部由数字组成，按数值排序；否则按字符串排序。

    Args:
        records: 记录列表
        id_fields: 主键字段名列表，默认为 ['ID', 'INDEX', 'SEQ', 'SEQUENCE']

    Returns:
        排序后的记录列表
    """
    if not records:
        return records

    if id_fields is None:
        id_fields = ["ID", "INDEX", "SEQ", "SEQUENCE"]

    def sort_key(record: Dict[str, Any]) -> tuple:
        # 检查是否有主键字段
        for field in id_fields:
            if field in record:
                val = record[field]
                num = try_parse_int(val)
                if num is not None:
                    return (0, 0, num)  # (优先级, 类型标志:0数字, 数值)
                else:
                    return (0, 1, str(val))  # (优先级, 类型标志:1字符串, 字符串值)

        # 没有主键字段，按第一条字段值排序（按字段名字母顺序取第一个）
        if record:
            first_key = sorted(record.keys())[0]
            val = record[first_key]
            num = try_parse_int(val)
            if num is not None:
                return (1, 0, num)
            else:
                return (1, 1, str(val))

        return (2, 1, "")  # 空记录放最后

    return sorted(records, key=sort_key)


def sort_configs(configs: List[Dict], id_fields: List[str] = None) -> List[Dict]:
    """
    对配置记录列表进行升序排序（基于 values 字段）

    Args:
        configs: 配置字典列表，每个字典包含 'values' 字段
        id_fields: 主键字段名列表

    Returns:
        排序后的配置列表
    """
    if not configs:
        return configs

    if id_fields is None:
        id_fields = ["ID", "INDEX", "SEQ", "SEQUENCE"]

    def sort_key(config: Dict) -> tuple:
        values = config.get("values", {})
        if not values:
            return (2, 1, "")

        # 检查是否有主键字段
        for field in id_fields:
            if field in values:
                val = values[field]
                num = try_parse_int(val)
                if num is not None:
                    return (0, 0, num)
                else:
                    return (0, 1, str(val))

        # 没有主键字段，按第一条字段值排序
        first_key = sorted(values.keys())[0]
        val = values[first_key]
        num = try_parse_int(val)
        if num is not None:
            return (1, 0, num)
        else:
            return (1, 1, str(val))

    return sorted(configs, key=sort_key)
