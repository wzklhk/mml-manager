# -*- coding: utf-8 -*-
"""
IO处理模块。

提供统一的文件读写接口和统计输出功能。
"""

import os
from typing import (
    Dict,
    List,
    Optional,
)
from datetime import (
    datetime,
)
from utils.table import (
    MmlDataSet,
    TableGroup,
    MmlConfig,
)
from utils.parse import (
    parse_any_command,
)

# --- MML文件读取 ---


def read_mml_file(
    file_path: str,
    encoding: str = "utf-8",
) -> MmlDataSet:
    """
    读取MML文件并解析为数据集。

    Args:
        file_path: MML文件路径
        encoding: 文件编码

    Returns:
        解析后的 MmlDataSet
    """
    dataset = MmlDataSet()
    with open(
        file_path,
        "r",
        encoding=encoding,
    ) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("--") or line.startswith("ENTER"):
                continue
            if line.startswith("SET") or line.startswith("ADD"):
                config_dict = parse_any_command(line)
                if config_dict:
                    dataset.add_from_dict(config_dict)
    return dataset


# --- MML文件写入 ---


def write_mml_file(
    file_path: str,
    dataset: MmlDataSet,
    source_desc: str = "",
    cmd_type: str = "SET",
    add_comments: bool = True,
    sort_groups: bool = True,
):
    """
    将数据集写入MML文件。

    Args:
        file_path: 输出文件路径
        dataset: 要写入的数据集
        source_desc: 来源描述（用于文件头注释）
        cmd_type: 命令类型（仅用于注释）
        add_comments: 是否添加头部注释
        sort_groups: 是否按字母序输出表分组
    """
    os.makedirs(
        os.path.dirname(os.path.abspath(file_path)),
        exist_ok=True,
    )

    from utils.mml import (
        format_mml_command,
    )

    with open(
        file_path,
        "w",
        encoding="utf-8",
    ) as f:
        if add_comments:
            f.write(f"-- 由 {source_desc} 生成\n" if source_desc else "-- MML配置数据\n")
            f.write(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- 命令类型: {cmd_type}\n\n")

        tables = dataset.tables if sort_groups else list(dataset._groups.keys())
        for table_name in tables:
            group = dataset.get_group(table_name)
            if not group:
                continue
            f.write(f"-- ===== {table_name} =====\n")
            for config in group.configs:
                line = format_mml_command(
                    config.cmd_type,
                    config.table,
                    config.values,
                )
                f.write(line + "\n")
            f.write("\n")

    print(f"[OK] MML文件已生成: {file_path}")


# --- 统计输出 ---


def print_statistics(
    dataset: MmlDataSet,
    title: str = "解析完成",
):
    """
    打印转换统计信息。

    Args:
        dataset: 数据集
        title: 统计标题
    """
    print(f"\n{title}:")
    for table in dataset.tables:
        group = dataset.get_group(table)
        if group:
            print(f"  - {table:<30} : {group.count:>4} 条")
    print(f"  - {'总计':<30} : {dataset.total_count:>4} 条")


def ensure_output_path(
    input_path: str,
    output_arg: Optional[str],
    default_ext: str = ".xlsx",
) -> str:
    """
    确定输出文件路径。

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
    return os.path.join(
        input_dir,
        f"{input_name}{default_ext}",
    )


def print_banner(
    title: str,
    **info,
):
    """打印格式化的标题和信息"""
    print("=" * 60)
    print(title)
    print("=" * 60)
    for (
        key,
        val,
    ) in info.items():
        print(f"{key}: {val}")
    print()


def print_footer():
    """打印结束分隔线"""
    print("\n" + "=" * 60)
    print("转换完成!")
    print("=" * 60)
