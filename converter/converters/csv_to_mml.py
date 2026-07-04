# -*- coding: utf-8 -*-
"""CSV → MML 转换核心模块"""

import os
from typing import Dict, List, Optional

from utils.mml import format_mml_value_simple


def row_to_mml(table_name: str, row: Dict, cmd_type: str = "SET") -> str:
    """将一行 CSV 数据转换为 MML 命令"""
    parts = [f"{k}={format_mml_value_simple(v)}" for k, v in row.items() if k.strip()]
    return f"{cmd_type} {table_name}:{','.join(parts)};" if parts else ""


def process_csv_file(csv_path: str, cmd_type_default: str = "SET") -> List[str]:
    """处理单个 CSV 文件，返回 MML 行列表"""
    import pandas as pd

    df = pd.read_csv(csv_path, dtype=str)
    df = df.fillna("")
    file_name = os.path.splitext(os.path.basename(csv_path))[0]
    mml_lines = [f"-- ===== {file_name} =====\n"]

    for _, row in df.iterrows():
        line = row_to_mml(file_name, row.to_dict(), cmd_type_default)
        if line:
            mml_lines.append(line + "\n")

    return mml_lines


def process_excel_file(excel_path: str, cmd_type_default: str = "SET") -> List[str]:
    """处理 Excel 文件，按 Sheet 名作为表名，返回 MML 行列表"""
    import pandas as pd

    xls = pd.ExcelFile(excel_path)
    mml_lines = []

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
        df = df.fillna("")
        table_name = sheet_name.replace(" ", "_")
        mml_lines.append(f"-- ===== {table_name} =====\n")

        for _, row in df.iterrows():
            line = row_to_mml(table_name, row.to_dict(), cmd_type_default)
            if line:
                mml_lines.append(line + "\n")
        mml_lines.append("\n")

    return mml_lines


def convert_to_mml(
    input_path: str,
    output_file: str,
    cmd_type: str = "SET",
) -> Dict:
    """转换 CSV 或 Excel 文件为 MML。

    Returns:
        {total, output_path}
    """
    ext = os.path.splitext(input_path)[1].lower()

    if ext in (".xlsx", ".xls"):
        mml_lines = process_excel_file(input_path, cmd_type)
    elif ext == ".csv":
        mml_lines = process_csv_file(input_path, cmd_type)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")

    # 统计 MML 行数
    total = sum(1 for l in mml_lines if l.startswith(("SET", "ADD")))

    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(mml_lines)

    return {"total": total, "output_path": output_file}
