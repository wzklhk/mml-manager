# -*- coding: utf-8 -*-
"""
通用CLI工具模块。

提供所有转换脚本通用的CLI参数定义、输出路径解析、文件校验等。
通过参数工厂模式减少各脚本CLI代码重复。
"""
import os
import argparse
from typing import Tuple, Optional


def add_input_output_args(parser: argparse.ArgumentParser,
                          input_help: str = '输入文件路径',
                          output_help: str = '输出文件路径',
                          require_input: bool = True):
    """
    添加通用的 --input / -o 参数。

    Args:
        parser: ArgumentParser实例
        input_help: input参数帮助文本
        output_help: output参数帮助文本
        require_input: input是否为必选
    """
    if require_input:
        parser.add_argument('input_file', help=input_help)
    else:
        parser.add_argument('input_file', nargs='?', default=None, help=input_help)
    parser.add_argument('-o', '--output', help=output_help)


def add_cmd_type_arg(parser: argparse.ArgumentParser):
    """添加 --cmd 命令类型参数"""
    parser.add_argument('--cmd', default='SET', choices=['SET', 'ADD'],
                        help='MML命令类型，默认: SET')


def add_encoding_arg(parser: argparse.ArgumentParser):
    """添加 --encoding 编码参数"""
    parser.add_argument('--encoding', default='utf-8',
                        help='文件编码（默认: utf-8）')


def resolve_output_path(input_path: str, output_arg: Optional[str],
                        default_ext: str = '.mml') -> str:
    """
    确定输出路径：优先用户指定，否则与输入文件同目录同名换扩展名。

    Args:
        input_path: 输入文件路径
        output_arg: 用户指定的输出路径（可为None）
        default_ext: 默认扩展名

    Returns:
        确定的输出路径
    """
    if output_arg:
        return output_arg
    input_dir = os.path.dirname(os.path.abspath(input_path))
    input_name = os.path.splitext(os.path.basename(input_path))[0]
    return os.path.join(input_dir, f"{input_name}{default_ext}")


def check_file_exists(file_path: str, label: str = "输入文件") -> bool:
    """
    检查文件是否存在，不存在则打印错误。

    Returns:
        True 表示存在，False 表示不存在
    """
    if not os.path.exists(file_path):
        print(f"❌ 错误: {label} '{file_path}' 不存在!")
        return False
    return True


def ensure_openpyxl():
    """检查openpyxl是否可用，不可用则退出"""
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        print("❌ 需要安装 openpyxl: pip install openpyxl")
        exit(1)
