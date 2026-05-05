#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计用户和套餐关系
输入：ADD PCCSub 格式的 MML 文件
输出：CSV 表格，包含套餐组合和用户数量
"""

import re
import sys
import csv
from collections import defaultdict
from pathlib import Path


def parse_pccsub_line(line: str):
    """解析 ADD PCCSub 行，返回 ISDN 和套餐列表"""
    line = line.strip()

    # 匹配 ADD PCCSub 命令（不区分大小写）
    match = re.match(r'(?i)ADD\s+PCCSub:(.+)', line)
    if not match:
        return None

    params_str = match.group(1)

    # 解析键值对：key=value,key2=value2,...
    params = {}
    # 使用正则提取，支持 quoted values (虽然套餐名通常不用引号)
    pattern = r'(\w+)=(?:"([^"]*)"|([^",]+))'
    for kv in re.finditer(pattern, params_str):
        key = kv.group(1)
        val = kv.group(2) if kv.group(2) is not None else kv.group(3)
        params[key] = val

    isdn = params.get('ISDN', '').strip()
    paknamelist = params.get('PAKNAMELIST', '').strip()

    if not isdn or not paknamelist:
        return None

    # 用 $ 分隔套餐名称
    pak_list = [p.strip() for p in paknamelist.split('$') if p.strip()]

    return isdn, pak_list


def analyze_packages(input_file: str, output_csv: str = None):
    """
    分析套餐组合统计

    Args:
        input_file: 输入文件路径，或 '-' 表示 stdin
        output_csv: 输出 CSV 文件路径，默认与输入文件同路径

    Returns:
        dict: 套餐组合 -> 用户数量
    """
    # 确定输入源
    if input_file == '-':
        f = sys.stdin
        lines = f.readlines()
    else:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

    # 统计：frozenset(套餐集合) -> 用户数
    pkg_combo_counts = defaultdict(int)
    # 同时记录：套餐名 -> 总用户数（单独统计）
    single_pkg_counts = defaultdict(int)
    total_users = 0
    processed_users = set()  # 去重：每个ISDN只算一次

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('--') or line.startswith('#'):
            continue

        result = parse_pccsub_line(line)
        if not result:
            continue

        isdn, pak_list = result

        # 去重：同一用户可能重复出现，只统计一次
        if isdn in processed_users:
            continue
        processed_users.add(isdn)

        total_users += 1

        if not pak_list:
            # 空套餐组合
            pkg_combo = frozenset()
            pkg_combo_counts[pkg_combo] += 1
            continue

        # 套餐组合（排序后转 frozenset 以确保相同集合相同 key）
        pkg_combo = frozenset(sorted(pak_list))
        pkg_combo_counts[pkg_combo] += 1

        # 单独统计每个套餐
        for pkg in pak_list:
            single_pkg_counts[pkg] += 1

    # 生成输出 CSV
    if output_csv is None:
        if input_file == '-':
            output_csv = 'package_combo_stats.csv'
        else:
            p = Path(input_file)
            output_csv = str(p.with_name(f"{p.stem}_package_combo_stats.csv"))

    # 写入 CSV（按用户数降序）
    with open(output_csv, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['套餐组合', '用户数量', '套餐数量'])

        # 排序：先按套餐数量降序，再按用户数降序
        sorted_combos = sorted(pkg_combo_counts.items(),
                              key=lambda x: (len(x[0]), x[1]),
                              reverse=True)

        for combo, count in sorted_combos:
            # 组合显示：排序后用 $ 连接（可改为逗号）
            combo_str = '$'.join(sorted(combo)) if combo else '(空套餐)'
            writer.writerow([combo_str, count, len(combo)])

    # 打印统计信息
    print(f"\n✅ 分析完成！")
    print(f"   输入文件: {input_file if input_file != '-' else 'stdin'}")
    print(f"   输出 CSV: {output_csv}")
    print(f"   总用户数（去重后）: {total_users}")
    print(f"   套餐组合数: {len(pkg_combo_counts)}")
    print(f"\n   前10个套餐组合（按用户数）:")
    for i, (combo, count) in enumerate(sorted_combos[:10], 1):
        combo_str = '$'.join(sorted(combo)) if combo else '(空套餐)'
        print(f"     {i}. {combo_str} : {count} 用户")

    return pkg_combo_counts, single_pkg_counts


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='统计用户套餐组合 - 分析 ADD PCCSub 文件中的套餐分布')
    parser.add_argument('input_file',
                        help='输入 MML 文件路径，或 "-" 表示标准输入')
    parser.add_argument('-o', '--output',
                        help='输出 CSV 文件路径（默认：输入文件同目录 *_package_combo_stats.csv）')

    args = parser.parse_args()

    analyze_packages(args.input_file, args.output)


if __name__ == "__main__":
    main()
