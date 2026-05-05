#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MML配置文件转Excel/CSV脚本

将MML配置文件（SET/ADD命令）转换为Excel (.xlsx) 或 CSV 格式。
每个表（table）对应一个Sheet（Excel）或一个文件（CSV）。

用法:
  # 默认生成Excel
  python mml2tabular.py input.mml

  # 只生成CSV
  python mml2tabular.py input.mml --csv

  # 同时生成Excel和CSV
  python mml2tabular.py input.mml --both

  # 指定输出前缀
  python mml2tabular.py input.mml -o my_output
"""
import os
import sys

# 确保可以从项目目录导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli_common import (
    add_input_output_args, add_encoding_arg,
    resolve_output_path, check_file_exists,
    ensure_openpyxl,
)
from utils.io_handler import (
    read_mml_file, print_statistics, print_banner, print_footer
)
from utils.sort import sort_configs
from tabular import write_excel, write_csvs


def convert(args):
    """执行转换"""
    ensure_openpyxl()

    # 读取MML文件
    dataset = read_mml_file(args.input_file, encoding=args.encoding)

    if dataset.total_count == 0:
        print("⚠️ 未找到有效的MML命令（SET/ADD），请检查文件格式")
        return

    print_statistics(dataset)

    # 排序
    for table in dataset.tables:
        group = dataset.get_group(table)
        if group:
            group.configs = sort_configs(
                [c.to_dict() for c in group.configs]
            )
            # 转回MmlConfig对象
            from utils.table import MmlConfig
            group.configs = [MmlConfig.from_dict(d) for d in group.configs]

    print(f"\n已对每个表的记录进行升序排序")

    # 确定输出基础路径（不含扩展名）
    output_base = resolve_output_path(args.input_file, args.output, default_ext='')

    generate_excel = False
    generate_csv = False
    if args.csv:
        generate_csv = True
    elif args.both:
        generate_excel = True
        generate_csv = True
    else:
        generate_excel = True

    # 输出Excel
    if generate_excel:
        excel_path = f"{output_base}.xlsx"
        write_excel(excel_path, dataset)

    # 输出CSV
    if generate_csv:
        csv_dir = f"{output_base}_csv"
        write_csvs(csv_dir, dataset)

    return dataset


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='MML配置文件转Excel/CSV脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 默认生成Excel
  python mml2tabular.py input.mml

  # 只生成CSV
  python mml2tabular.py input.mml --csv

  # 同时生成Excel和CSV
  python mml2tabular.py input.mml --both

  # 指定输出文件名前缀
  python mml2tabular.py input.mml -o my_output
        """
    )

    add_input_output_args(parser,
                          input_help='输入的MML配置文件路径',
                          output_help='输出的文件基础路径（不含扩展名）')
    add_encoding_arg(parser)

    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument('--excel', action='store_true', default=True,
                              help='生成Excel文件 (默认)')
    output_group.add_argument('--csv', action='store_true',
                              help='只生成CSV文件')
    output_group.add_argument('--both', action='store_true',
                              help='同时生成Excel和CSV文件')

    args = parser.parse_args()

    if not args.input_file:
        parser.print_help()
        return

    if not check_file_exists(args.input_file):
        return

    print_banner("MML配置文件转Excel/CSV脚本",
                 输入文件=args.input_file)
    convert(args)
    print_footer()


if __name__ == '__main__':
    main()
