# -*- coding: utf-8 -*-
"""Combo 包分析模块 — 解析 PCCSUB 等组合包配置"""

import re
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


def parse_pccsub_line(line: str) -> Optional[Dict]:
    """解析 PCCSUB/COMBO 行。

    示例:
    PCCSUB:"PKG_MCC_01",MCC="460",MNC="00";

    Returns:
        {'pkg_name': 'PKG_MCC_01', 'params': {'MCC': '460', 'MNC': '00'}}
    """
    line = line.strip()
    if not line or line.startswith("--"):
        return None

    # PCCSUB:"NAME",KEY="VAL",KEY="VAL";
    match = re.match(r'(PCCSUB|COMBO|PKG):\s*"([^"]+)"\s*,?\s*(.*?);?\s*$', line, re.IGNORECASE)
    if not match:
        return None

    pkg_name = match.group(2)
    params_str = match.group(3)

    params = {}
    pattern = r'(\w+)\s*=\s*"([^"]*)"'
    for m in re.finditer(pattern, params_str):
        params[m.group(1)] = m.group(2)

    return {"pkg_name": pkg_name, "params": params}


def analyze_packages(input_file: str, output_csv: str = None) -> Dict:
    """分析组合包配置文件。

    Args:
        input_file: MML 配置文件路径
        output_csv: 可选输出 CSV 路径

    Returns:
        分析统计: {total_packages, packages: [{pkg_name, params, param_count}], columns}
    """
    packages = []
    all_params = set()

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            pkg = parse_pccsub_line(line)
            if pkg:
                packages.append(pkg)
                all_params.update(pkg["params"].keys())

    result = {
        "total_packages": len(packages),
        "packages": [],
        "columns": sorted(all_params),
    }

    for pkg in packages:
        entry = {
            "pkg_name": pkg["pkg_name"],
            "params": pkg["params"],
            "param_count": len(pkg["params"]),
        }
        result["packages"].append(entry)

    # 写入 CSV
    if output_csv and packages:
        columns = ["pkg_name"] + sorted(all_params)
        with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for pkg in packages:
                row = {"pkg_name": pkg["pkg_name"]}
                row.update(pkg["params"])
                writer.writerow(row)

    return result
