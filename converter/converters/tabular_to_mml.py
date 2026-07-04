# -*- coding: utf-8 -*-
"""Tabular (Excel/CSV) → MML 转换核心模块"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional

from utils.io_handler import write_mml_file
from converters.mml_to_sql import parse_any_command
from tabular import read_excel, read_csv, read_csv_batch
from cli_common import resolve_output_path


def convert_excel(
    input_file: str,
    output_dir: str,
    cmd_type: str = "SET",
    encoding: str = "utf-8",
    pick_fields: Optional[List[str]] = None,
) -> int:
    """转换 Excel 文件为 MML。

    Returns:
        处理的行数
    """
    dataset = read_excel(input_file, pick_fields=pick_fields)
    if dataset.total_count == 0:
        raise ValueError(f'Excel文件 "{input_file}" 中没有有效数据')

    output_name = os.path.splitext(os.path.basename(input_file))[0] + ".mml"
    output_path = os.path.join(output_dir, output_name)

    for group in dataset.tables:
        g = dataset.get_group(group)
        if g:
            for c in g.configs:
                c.cmd_type = cmd_type

    write_mml_file(
        output_path, dataset, source_desc=f"tabular2mml.py 从 {os.path.basename(input_file)}", cmd_type=cmd_type
    )
    return dataset.total_count


def convert_csv(
    input_file: str,
    output_dir: str,
    cmd_type: str = "SET",
    table_name: str = None,
    pick_fields: Optional[List[str]] = None,
) -> int:
    """转换 CSV 文件为 MML。

    Returns:
        处理的行数
    """
    dataset = read_csv(input_file, table_name=table_name, pick_fields=pick_fields)
    if dataset.total_count == 0:
        raise ValueError(f'CSV文件 "{input_file}" 中没有有效数据')

    output_name = os.path.splitext(os.path.basename(input_file))[0] + ".mml"
    output_path = os.path.join(output_dir, output_name)

    for group in dataset.tables:
        g = dataset.get_group(group)
        if g:
            for c in g.configs:
                c.cmd_type = cmd_type

    write_mml_file(
        output_path, dataset, source_desc=f"tabular2mml.py 从 {os.path.basename(input_file)}", cmd_type=cmd_type
    )
    return dataset.total_count
