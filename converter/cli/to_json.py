#!//usr/bin/env python3
"""
CLI: MML → JSON 转换
用法: python -m cli.to_json input.mml [-o output.json] [--encoding utf-8]
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse

from converters.mml_to_json import convert_file_to_json
from cli.utils import ensure_input_file, resolve_output_path, add_common_args


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='MML → JSON 转换')
    parser.add_argument('input_file', help='输入的MML文件路径')
    add_common_args(parser)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not ensure_input_file(args.input_file):
        return

    output = resolve_output_path(args.input_file, args.output, '.json')
    meta = convert_file_to_json(args.input_file, output, args.encoding)

    print(f"[OK] JSON文件: {output}")
    print(f"     共 {meta['total_configs']} 条配置")


if __name__ == '__main__':
    main()
