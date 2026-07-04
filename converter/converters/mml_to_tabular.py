# -*- coding: utf-8 -*-
"""MML → Tabular (Excel/CSV) 转换核心模块"""

import os
from typing import Dict, List, Optional

from converters.mml_to_sql import parse_mml_file
from utils.sort import sort_configs
from utils.io_handler import print_statistics
from tabular import write_excel, write_csvs
from utils.table import MmlConfig


def convert_numeric_strings(value):
    """尝试将数字字符串转为数值类型"""
    if value is None:
        return ""
    try:
        if "." in str(value):
            return float(value)
        return int(value)
    except (ValueError, TypeError):
        return value


def convert(
    input_file: str,
    output_base: str = None,
    generate_excel: bool = True,
    generate_csv: bool = False,
    encoding: str = "utf-8",
) -> Dict:
    """转换 MML 文件为 Excel/CSV。

    Args:
        input_file: 输入的 MML 文件路径
        output_base: 输出文件基础路径（不含扩展名），默认与输入同目录同名
        generate_excel: 是否生成 Excel
        generate_csv: 是否生成 CSV
        encoding: 文件编码

    Returns:
        {output_excel, output_csv_dir, config_count, table_count}
    """
    from utils.io_handler import read_mml_file

    dataset = read_mml_file(input_file, encoding=encoding)
    if dataset.total_count == 0:
        raise ValueError("未找到有效的MML命令")

    # 排序
    for table in dataset.tables:
        group = dataset.get_group(table)
        if group:
            group.configs = sort_configs([c.to_dict() for c in group.configs])
            group.configs = [MmlConfig.from_dict(d) for d in group.configs]

    if output_base is None:
        base = os.path.splitext(input_file)[0]
    else:
        base = output_base

    result = {"config_count": dataset.total_count, "table_count": len(dataset.tables)}

    if generate_excel:
        excel_path = f"{base}.xlsx"
        write_excel(excel_path, dataset)
        result["output_excel"] = excel_path

    if generate_csv:
        csv_dir = f"{base}_csv"
        write_csvs(csv_dir, dataset)
        result["output_csv_dir"] = csv_dir

    return result
