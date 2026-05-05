#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON文件转MML配置文件
将MongoDB JSON格式（或多表结构JSON）还原为MML命令
支持命令行参数指定输入文件
"""

import json
import argparse
import os
from datetime import datetime

def escape_mml_value(value: str) -> str:
    """转义MML值中的双引号"""
    if value is None:
        return 'NULL'
    if not isinstance(value, str):
        return str(value)
    # 如果值包含空格、逗号或;双引号，需要加引号
    if re.search(r'[\s,;"]', value):
        escaped = value.replace('"', '""')
        return f'"{escaped}"'
    return value

def convert_json_to_mml(json_file: str, output_file: str, encoding: str = 'utf-8'):
    """
    将JSON文件转换为MML命令

    Args:
        json_file: 输入的JSON文件路径
        output_file: 输出的MML文件路径
        encoding: 文件编码
    """
    print(f"正在读取JSON文件: {json_file}")

    with open(json_file, 'r', encoding=encoding) as f:
        data = json.load(f)

    # 支持两种JSON结构：
    # 1. 我们生成的：{"metadata": {...}, "data": {"TABLE1": [...], "TABLE2": [...]}}
    # 2. 直接的表列表或文档数组（回退处理）

    mml_lines = []
    table_stats = {}

    if isinstance(data, dict) and 'data' in data and isinstance(data['data'], dict):
        # 结构1: 按表分组
        data_by_table = data['data']
        for table_name, documents in data_by_table.items():
            if not isinstance(documents, list):
                continue
            for doc in documents:
                if not isinstance(doc, dict):
                    continue
                # 生成命令：含ID的表用ADD，否则SET
                if 'ID' in doc and table_name not in ['SCTPGLOBAL']:
                    cmd_type = 'ADD'
                else:
                    cmd_type = 'SET'

                kv_pairs = []
                for key, val in doc.items():
                    val_str = escape_mml_value(val)
                    kv_pairs.append(f"{key}={val_str}")

                mml_line = f"{cmd_type} {table_name}:{','.join(kv_pairs)};"
                mml_lines.append(mml_line)

            table_stats[table_name] = table_stats.get(table_name, 0) + len(documents)
    else:
        # 结构2: 直接数组或字典，假设是单个表的文档数组
        documents = data if isinstance(data, list) else [data]
        table_name = "TABLE"  # 默认表名，需要用户指定？
        for doc in documents:
            if not isinstance(doc, dict):
                continue
            if 'ID' in doc and table_name not in ['SCTPGLOBAL']:
                cmd_type = 'ADD'
            else:
                cmd_type = 'SET'

            kv_pairs = []
            for key, val in doc.items():
                val_str = escape_mml_value(val)
                kv_pairs.append(f"{key}={val_str}")

            mml_line = f"{cmd_type} {table_name}:{','.join(kv_pairs)};"
            mml_lines.append(mml_line)

        table_stats[table_name] = len(documents)

    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(mml_lines))

    print(f"\n[OK] MML文件已生成: {output_file}")
    print(f"   总命令数: {len(mml_lines)}")
    print("   各表统计:")
    for table, count in sorted(table_stats.items()):
        print(f"     {table:<20} : {count:>4} 条")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='JSON文件转MML配置文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法
  python json2mml.py input.json

  # 指定输出文件
  python json2mml.py input.json -o output.mml

  # 指定编码
  python json2mml.py input.json --encoding gbk
        """
    )

    parser.add_argument('input_file', nargs='?', help='输入的JSON文件路径')
    parser.add_argument('-o', '--output', help='输出的MML文件路径（默认：同名.mml）')
    parser.add_argument('--encoding', default='utf-8', help='文件编码（默认：utf-8）')

    args = parser.parse_args()

    if not args.input_file:
        parser.print_help()
        return

    if not os.path.exists(args.input_file):
        print(f"❌ 错误: 输入文件不存在!")
        print(f"   路径: {args.input_file}")
        return

    input_dir = os.path.dirname(os.path.abspath(args.input_file))
    input_name = os.path.splitext(os.path.basename(args.input_file))[0]

    output_mml = args.output if args.output else os.path.join(input_dir, f"{input_name}.mml")

    print("=" * 60)
    print("JSON文件转MML")
    print("=" * 60)
    print(f"\n输入文件: {args.input_file}")
    print(f"输出MML:  {output_mml}")
    print(f"编码: {args.encoding}")
    print()

    try:
        convert_json_to_mml(args.input_file, output_mml, args.encoding)

        print("\n" + "=" * 60)
        print("转换完成!")
        print("=" * 60)
        print(f"\n生成的文件: {output_mml}")
    except Exception as e:
        print(f"\n[ERROR] 错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()