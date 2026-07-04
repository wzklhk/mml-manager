#!//usr/bin/env python3
"""
CLI: MML → SQL 转换
用法: python -m cli.to_sql input.mml [-o output.sql] [--encoding utf-8]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse

from converters.mml_to_sql import convert_file_to_sql, list_commands_in_file
from cli.utils import ensure_input_file, resolve_output_path, add_common_args


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MML → SQL 转换")
    parser.add_argument("input_file", help="输入的MML文件路径")
    add_common_args(parser)
    parser.add_argument("-d", "--database", help="同时生成SQLite数据库文件")
    parser.add_argument("--sql-only", action="store_true", help="只生成SQL脚本，不生成DB")
    parser.add_argument("--list-commands", action="store_true", help="只列出命令类型统计")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not ensure_input_file(args.input_file):
        return

    if args.list_commands:
        info = list_commands_in_file(args.input_file, args.encoding)
        print("命令类型统计:")
        for cmd, count in sorted(info["command_types"].items()):
            print(f"  {cmd:<30} : {count:>4} 条")
        return

    output = resolve_output_path(args.input_file, args.output, ".sql")
    db_name = args.database

    total, tables = convert_file_to_sql(
        args.input_file,
        output,
        db_name if not args.sql_only else None,
        args.encoding,
    )

    print(f"[OK] SQL文件: {output}")
    print(f"     共 {total} 条配置, {tables} 个表")


if __name__ == "__main__":
    main()
