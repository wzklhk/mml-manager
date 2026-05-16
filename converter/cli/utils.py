# -*- coding: utf-8 -*-
"""CLI 工具包 — 共享工具函数"""
import os
import sys
import argparse
from typing import Optional


def ensure_input_file(input_path: str) -> bool:
    """检查输入文件是否存在，不存在则打印错误"""
    if not os.path.exists(input_path):
        print(f"❌ 输入文件不存在: {input_path}")
        return False
    return True


def resolve_output_path(
    input_path: str,
    output_arg: Optional[str],
    default_ext: str,
    output_dir: Optional[str] = None,
) -> str:
    """确定输出路径：
    优先用户指定，否则与输入文件同目录同名换扩展名。
    """
    if output_arg:
        return output_arg
    base = os.path.splitext(input_path)[0]
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, os.path.basename(base) + default_ext)
    return base + default_ext


def add_common_args(parser: argparse.ArgumentParser):
    """添加通用的 -o/--output 和 --encoding 参数"""
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('--encoding', default='utf-8', help='文件编码（默认 utf-8）')
