#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel/CSV文件转MML配置命令脚本

支持将Excel (.xlsx) 或 CSV 文件转换回MML配置命令格式。
每个Sheet（Excel）或每个CSV文件对应一个表。

用法:
  # Excel 转 MML
  python tabular2mml.py input.xlsx

  # CSV 转 MML
  python tabular2mml.py data.csv -o output.mml

  # 使用ADD命令
  python tabular2mml.py data.csv --cmd ADD

  # 指定表名（CSV模式）
  python tabular2mml.py data.csv --table MY_TABLE

  # 批量转换目录下所有CSV
  python tabular2mml.py ./csv_dir/ --batch
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli_common import (
    add_cmd_type_arg, add_encoding_arg,
    resolve_output_path, check_file_exists,
    ensure_openpyxl,
)
from utils.io_handler import (
    write_mml_file, print_banner, print_footer
)
from tabular import read_excel, read_csv, read_csv_batch


def convert_excel(args) -> int:
    """Excel转MML"""
    ensure_openpyxl()
    ds = read_excel(args.input_file, sheet_names=args.sheets)
    if ds.total_count == 0:
        print("⚠️ 未读取到数据")
        return 0

    # 统一命令类型
    for table in ds.tables:
        group = ds.get_group(table)
        if group:
            for c in group.configs:
                c.cmd_type = args.cmd

    output_path = resolve_output_path(args.input_file, args.output)
    write_mml_file(output_path, ds,
                   source_desc=f"tabular2mml.py 从 {os.path.basename(args.input_file)}",
                   cmd_type=args.cmd)
    print(f"总计: {ds.total_count} 条配置命令")
    return ds.total_count


def convert_csv(args) -> int:
    """单个CSV转MML"""
    table_name = args.table
    if table_name is None:
        import re
        table_name = re.sub(r'[^a-zA-Z0-9_]', '_',
                            os.path.splitext(os.path.basename(args.input_file))[0])
        if not table_name or table_name[0].isdigit():
            table_name = f"T_{table_name}"

    ds = read_csv(args.input_file, table_name=table_name)
    if ds.total_count == 0:
        print("⚠️ 未读取到数据")
        return 0

    for table in ds.tables:
        group = ds.get_group(table)
        if group:
            for c in group.configs:
                c.cmd_type = args.cmd

    output_path = resolve_output_path(args.input_file, args.output)
    write_mml_file(output_path, ds,
                   source_desc=f"tabular2mml.py 从 {os.path.basename(args.input_file)}",
                   cmd_type=args.cmd)
    print(f"总计: {ds.total_count} 条配置命令")
    return ds.total_count


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Excel/CSV文件转MML配置命令脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # Excel 转 MML
  python tabular2mml.py input.xlsx

  # CSV 转 MML
  python tabular2mml.py data.csv -o output.mml --table LTE_CELL

  # 使用ADD命令
  python tabular2mml.py data.csv --cmd ADD

  # 批量转换目录下所有CSV
  python tabular2mml.py ./csv_dir/ --batch

  # 仅处理Excel的指定Sheet
  python tabular2mml.py input.xlsx --sheets LTE_CELL LTE_PARAM
        """
    )

    parser.add_argument('input_file',
                        help='输入的Excel(.xlsx)或CSV文件/目录(batch模式)')
    parser.add_argument('-o', '--output',
                        help='输出MML文件路径（单个模式）或输出目录（batch模式）')
    add_cmd_type_arg(parser)
    parser.add_argument('--table',
                        help='表名（CSV模式有效，默认使用文件名）')
    parser.add_argument('--sheets', nargs='*',
                        help='Excel中要处理的Sheet名（不指定则处理全部）')
    parser.add_argument('--batch', action='store_true',
                        help='批量模式：转换目录下所有CSV文件')

    args = parser.parse_args()

    if not check_file_exists(args.input_file):
        return

    ext = os.path.splitext(args.input_file)[1].lower()

    # 批量模式
    if args.batch:
        if not os.path.isdir(args.input_file):
            print("❌ 错误: batch模式需要一个目录路径")
            return
        output_dir = args.output or os.path.join(args.input_file, 'mml_output')
        print_banner("CSV批量转MML配置命令",
                     输入目录=args.input_file,
                     输出目录=output_dir,
                     命令类型=args.cmd)
        read_csv_batch(args.input_file, output_dir, cmd_type=args.cmd)
        print_footer()
        return

    # 单个文件模式
    if ext in ('.csv',):
        title = "CSV转MML配置命令"
    elif ext in ('.xlsx', '.xls'):
        title = "Excel转MML配置命令"
        ensure_openpyxl()
    else:
        print(f"⚠️ 不支持的文件格式: {ext}")
        print(f"   支持: .xlsx, .xls, .csv")
        return

    print_banner(title,
                 输入文件=args.input_file,
                 命令类型=args.cmd)

    if ext in ('.csv',):
        count = convert_csv(args)
    else:
        count = convert_excel(args)

    if count > 0:
        print_footer()


if __name__ == '__main__':
    main()
