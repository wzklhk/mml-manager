# -*- coding: utf-8 -*-
"""
公共工具模块

提供MML转换器的通用功能分层：
- mml:    MML值格式化与命令生成
- parse:  MML命令解析
- sort:   记录排序
- table:  表名处理与数据模型
- io_handler: 文件读写与统计
"""

from .parse import (
    parse_key_value_pairs,
    parse_any_command,
    parse_mml_file,
)

from .sort import (
    sort_records,
    sort_configs,
    try_parse_int,
)

from .mml import (
    quote_mml_value,
    format_mml_command,
    format_mml_value_simple,
)

from .table import (
    sanitize_table_name,
    MmlConfig,
    TableGroup,
    MmlDataSet,
)

from .io_handler import (
    read_mml_file,
    write_mml_file,
    print_statistics,
    ensure_output_path,
    print_banner,
    print_footer,
)

__all__ = [
    # parse
    "parse_key_value_pairs",
    "parse_any_command",
    "parse_mml_file",
    # sort
    "sort_records",
    "sort_configs",
    "try_parse_int",
    # mml
    "quote_mml_value",
    "format_mml_command",
    "format_mml_value_simple",
    # table
    "sanitize_table_name",
    "MmlConfig",
    "TableGroup",
    "MmlDataSet",
    # io_handler
    "read_mml_file",
    "write_mml_file",
    "print_statistics",
    "ensure_output_path",
    "print_banner",
    "print_footer",
]
