#!//usr/bin/env python3
"""
CLI: MML → Excel/CSV 转换
用法: python -m cli.to_xls input.mml [-o output_base] [--csv|--both]
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse

from converters.mml_to_xls import convert_file_to_excel_and_csv
from cli.utils import ensure_input_file, add_common_args


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='MML → Excel/CSV 转换')
    parser.add_argument('input_file', help='输入的MML文件路径')
    add_common_args(parser)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--excel', action='store_true', default=True, help='生成Excel (默认)')
    group.add_argument('--csv', action='store_true', help='只生成CSV')
    group.add_argument('--both', action='store_true', help='同时生成Excel和CSV')
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not ensure_input_file(args.input_file):
        return

    output_base = args.output or os.path.splitext(args.input_file)[0]
    # 如果用户传了 -o file.xlsx，去掉扩展名避免双后缀
    if output_base.endswith('.xlsx'):
        output_base = output_base[:-5]
    gen_excel = args.excel or args.both or not args.csv
    gen_csv = args.csv or args.both

    result = convert_file_to_excel_and_csv(
        args.input_file, output_base,
        generate_excel=gen_excel, generate_csv=gen_csv,
        encoding=args.encoding,
    )

    print(f"[OK] 共 {result['total']} 条配置, {len(result['tables'])} 个表")
    if 'excel_path' in result:
        print(f"     Excel: {result['excel_path']}")
    if 'csv_dir' in result:
        print(f"     CSV目录: {result['csv_dir']}")


if __name__ == '__main__':
    main()
