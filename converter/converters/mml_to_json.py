# -*- coding: utf-8 -*-
"""MML → JSON 转换核心模块"""

import json
import os
from datetime import datetime
from typing import Dict, List

from converters.mml_to_sql import parse_mml_file, sort_configs_by_values
from utils.parse import parse_any_command as util_parse
from utils.sort import sort_records


def convert_file_to_json(
    input_file: str,
    output_file: str,
    encoding: str = "gbk",
) -> Dict:
    """转换 MML 文件为 JSON。

    返回统计信息: {total, tables: {table_name: count}}
    """
    configs_by_table, all_columns = parse_mml_file(input_file, encoding)
    total = sum(len(v) for v in configs_by_table.values())

    result = {
        "meta": {
            "source": os.path.basename(input_file),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_configs": total,
        },
        "configs": {},
    }

    for table_name in sorted(configs_by_table.keys()):
        configs = configs_by_table[table_name]
        result["configs"][table_name] = [{"cmd_type": c["cmd_type"], "values": c["values"]} for c in configs]

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result["meta"]
