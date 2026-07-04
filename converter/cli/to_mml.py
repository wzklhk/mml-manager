#!//usr/bin/env python3
"""
CLI: 各种格式 → MML 统一转换

用法:
  python -m cli.to_mml input.sql [-o output.mml]                    # SQL 转 MML
  python -m cli.to_mml input.csv [-o output.mml]                    # CSV 转 MML
  python -m cli.to_mml input.json [-o output.mml]                   # JSON 转 MML
  python -m cli.to_mml input.xlsx [-o output.mml]                   # Excel 转 MML
  python -m cli.to_mml input.xlsx --type tabular [-o output_dir/]   # Excel 多表转 MML
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse

from cli.utils import ensure_input_file, add_common_args


def _convert_sql(input_file: str, output: str, encoding: str, cmd_type: str):
    from converters.sql_to_mml import convert_sql_file

    dataset = convert_sql_file(input_file, output, cmd_type, encoding)
    return dataset.total_count


def _convert_json(input_file: str, output: str, encoding: str):
    from converters.json_to_mml import convert_json_to_mml

    result = convert_json_to_mml(input_file, output, encoding)
    return result["total"]


def _convert_csv(input_file: str, output: str, cmd_type: str):
    from converters.csv_to_mml import convert_to_mml

    result = convert_to_mml(input_file, output, cmd_type)
    return result["total"]


def _convert_xls(input_file: str, output: str):
    from converters.xls_to_mml import convert_xls_to_mml

    result = convert_xls_to_mml(input_file, output)
    return result["total"]


def _convert_tabular(input_file: str, output_dir: str, cmd_type: str, table: str):
    from converters.tabular_to_mml import convert_excel, convert_csv

    ext = os.path.splitext(input_file)[1].lower()
    if ext in (".xlsx", ".xls"):
        return convert_excel(input_file, output_dir, cmd_type)
    else:
        return convert_csv(input_file, output_dir, cmd_type, table)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="各种格式 → MML 转换")
    parser.add_argument("input_file", help="输入文件路径")
    add_common_args(parser)
    parser.add_argument("--cmd", default="SET", choices=["SET", "ADD"], help="MML命令类型")
    parser.add_argument(
        "--type",
        choices=["auto", "sql", "json", "csv", "xls", "tabular"],
        default="auto",
        help="输入格式（默认自动检测）",
    )
    parser.add_argument("--table", help="指定表名（CSV模式）")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not ensure_input_file(args.input_file):
        return

    ext = os.path.splitext(args.input_file)[1].lower()
    input_type = args.type

    if input_type == "auto":
        type_map = {".sql": "sql", ".json": "json", ".csv": "csv", ".xlsx": "tabular", ".xls": "xls"}
        input_type = type_map.get(ext, "tabular")

    handlers = {
        "sql": _convert_sql,
        "json": _convert_json,
        "csv": _convert_csv,
        "xls": _convert_xls,
        "tabular": _convert_tabular,
    }

    handler = handlers.get(input_type)
    if not handler:
        print(f"❌ 不支持的格式: {ext}")
        return

    output = args.output or os.path.splitext(args.input_file)[0] + ".mml"

    if input_type == "tabular":
        output_dir = args.output or os.path.join(os.path.dirname(args.input_file), "mml_output")
        os.makedirs(output_dir, exist_ok=True)
        count = handler(args.input_file, output_dir, args.cmd, args.table)
        print(f"[OK] 转换完成: {count} 条 → {output_dir}/")
    elif input_type == "sql":
        count = handler(args.input_file, output, args.encoding, args.cmd)
        print(f"[OK] MML文件: {output}  ({count} 条)")
    else:
        count = handler(args.input_file, output, args.encoding)
        print(f"[OK] MML文件: {output}  ({count} 条)")


if __name__ == "__main__":
    main()
