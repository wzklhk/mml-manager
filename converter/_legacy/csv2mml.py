#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV文件转MML配置命令脚本

将CSV文件转换回MML配置命令格式。
支持批量处理目录下所有CSV文件，每个文件对应一个表名。

用法:
  # 单个CSV转MML
  python csv2mml.py data.csv

  # 指定输出文件和表名
  python csv2mml.py data.csv -o output.mml --table MY_TABLE

  # 使用ADD命令
  python csv2mml.py data.csv --cmd ADD

  # 批量转换目录下所有CSV
  python csv2mml.py ./data/ --batch
"""
import os
import re
import csv
import argparse
from typing import Optional, List


def quote_mml_value(value) -> str:
    """
    将值格式化为MML值
    - None/空 -> ''
    - 数字 -> 直接转为字符串
    - 字符串 -> 如果包含空格、逗号、分号或双引号，加双引号并转义
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


def sanitize_table_name(name: str) -> str:
    """将文件名或字符串转为合法的MML表名"""
    table = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    if not table or table[0].isdigit():
        table = f"T_{table}"
    return table


def convert_csv_to_mml(input_path: str, output_path: str, cmd_type: str = 'SET', table_name: Optional[str] = None):
    """
    将CSV文件转换为MML配置命令

    Args:
        input_path: CSV文件路径
        output_path: 输出MML文件路径
        cmd_type: MML命令类型 (SET/ADD)
        table_name: 目标表名，默认使用CSV文件名
    """
    print(f"正在读取CSV文件: {input_path}")

    if table_name is None:
        table_name = sanitize_table_name(os.path.splitext(os.path.basename(input_path))[0])

    mml_lines = []
    count = 0

    try:
        with open(input_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            if not headers:
                print(f"⚠️ 警告: 文件 '{input_path}' 无有效列头，跳过")
                return

            valid_headers = [h.strip() for h in headers if h.strip()]

            for row_idx, row in enumerate(reader, 2):
                kv_pairs = []
                has_value = False

                for key in valid_headers:
                    val = row.get(key, '').strip() if row.get(key) else ''
                    if val:
                        has_value = True
                    val_str = quote_mml_value(val)
                    if val_str:
                        kv_pairs.append(f"{key}={val_str}")

                if not has_value:
                    continue

                if kv_pairs:
                    mml_line = f"{cmd_type} {table_name}:{','.join(kv_pairs)};"
                    # 注释标明来源行号
                    mml_lines.append(mml_line)
                    mml_lines.append(f"-- 来源: {os.path.basename(input_path)} 第{row_idx}行")
                    count += 1

    except Exception as e:
        print(f"❌ 错误: 读取CSV文件失败: {e}")
        return

    print(f"  - {table_name:<30} : {count:>4} 条")
    print(f"总计: {count} 条配置命令")

    # 写入输出文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"-- 由 csv2mml.py 从 {os.path.basename(input_path)} 生成\n")
        f.write(f"-- 生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- 命令类型: {cmd_type}\n")
        f.write(f"-- 表名: {table_name}\n\n")
        for line in mml_lines:
            f.write(line + '\n')

    print(f"[OK] MML文件已生成: {output_path}")


def batch_convert(input_dir: str, output_dir: str, cmd_type: str = 'SET'):
    """
    批量转换目录下所有CSV文件为MML

    Args:
        input_dir: CSV文件所在目录
        output_dir: 输出MML文件目录
        cmd_type: MML命令类型
    """
    os.makedirs(output_dir, exist_ok=True)
    csv_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.csv')]
    csv_files.sort()

    if not csv_files:
        print(f"⚠️ 目录 '{input_dir}' 中没有找到CSV文件")
        return

    print(f"找到 {len(csv_files)} 个CSV文件，开始批量转换...\n")

    total_all = 0
    for csv_file in csv_files:
        input_path = os.path.join(input_dir, csv_file)
        output_name = os.path.splitext(csv_file)[0] + '.mml'
        output_path = os.path.join(output_dir, output_name)
        print(f"[{csv_files.index(csv_file) + 1}/{len(csv_files)}] {csv_file}")
        convert_csv_to_mml(input_path, output_path, cmd_type=cmd_type)

        # 统计该文件的行数
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                lines = sum(1 for line in f if line.startswith(cmd_type))
                total_all += lines
        except Exception:
            pass
        print()

    print(f"批量转换完成! 共处理 {len(csv_files)} 个CSV文件，生成 {total_all} 条配置命令")


def main():
    parser = argparse.ArgumentParser(
        description='CSV文件转MML配置命令脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单个CSV转MML
  python csv2mml.py data.csv

  # 指定输出文件和表名
  python csv2mml.py data.csv -o config.mml --table LTE_CELL

  # 使用ADD命令
  python csv2mml.py data.csv --cmd ADD

  # 批量转换目录下所有CSV
  python csv2mml.py ./csv_files/ --batch

  # 批量模式指定输出目录
  python csv2mml.py ./csv_files/ --batch -o ./mml_output/
        """
    )

    parser.add_argument('input',
                        help='输入的CSV文件或目录路径')
    parser.add_argument('-o', '--output',
                        help='输出文件路径（单个模式）或输出目录（batch模式）')
    parser.add_argument('--cmd', default='SET', choices=['SET', 'ADD'],
                        help='MML命令类型，默认: SET')
    parser.add_argument('--table',
                        help='表名（默认使用CSV文件名）')
    parser.add_argument('--batch', action='store_true',
                        help='批量模式：转换目录下所有CSV文件')
    parser.add_argument('--encoding', default='utf-8',
                        help='CSV文件编码（默认: utf-8）')

    args = parser.parse_args()

    input_path = args.input

    if not os.path.exists(input_path):
        print(f"❌ 错误: 路径 '{input_path}' 不存在!")
        return

    print("=" * 60)
    print("CSV转MML配置命令脚本")
    print("=" * 60)
    print(f"输入: {input_path}")
    print(f"命令类型: {args.cmd}")
    print()

    if args.batch:
        # 批量模式
        if not os.path.isdir(input_path):
            print(f"❌ 错误: batch模式需要一个目录路径")
            return

        output_dir = args.output if args.output else os.path.join(input_path, 'mml_output')
        batch_convert(input_path, output_dir, cmd_type=args.cmd)
    else:
        # 单个文件模式
        if not os.path.isfile(input_path):
            print(f"❌ 错误: 请指定一个CSV文件路径")
            return

        if not input_path.lower().endswith('.csv'):
            print(f"⚠️ 警告: 文件扩展名不是 .csv，但将继续处理")

        input_dir = os.path.dirname(os.path.abspath(input_path))
        input_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = args.output if args.output else os.path.join(input_dir, f"{input_name}.mml")

        convert_csv_to_mml(input_path, output_path, cmd_type=args.cmd, table_name=args.table)

        print("\n" + "=" * 60)
        print("转换完成!")
        print("=" * 60)


if __name__ == '__main__':
    main()
