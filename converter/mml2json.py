#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MML配置文件转MongoDB JSON格式
将MML配置文件转换为JSON文件，便于用mongoimport导入MongoDB
支持命令行参数指定输入文件
"""

import re
import json
import argparse
from datetime import datetime
from typing import List, Dict
import os

from utils.parse import parse_any_command
from utils.sort import sort_records

def convert_file_to_json(input_file: str, output_file: str, encoding: str = 'gbk'):
    """
    转换配置文件为MongoDB JSON格式

    Args:
        input_file: 输入文件路径
        output_file: 输出JSON文件路径（将生成一个JSON文件，包含所有表的数据）
        encoding: 文件编码
    """
    print(f"正在读取文件: {input_file}")

    with open(input_file, 'r', encoding=encoding) as f:
        lines = f.readlines()

    # 统计数据 - 按表组织
    data_by_table = {}  # table_name -> list of data dicts

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('--'):
            continue

        if line.startswith('ENTER'):
            continue

        elif line.startswith('SET') or line.startswith('ADD'):
            config = parse_any_command(line)
            if config:
                table_name = config['table']
                if table_name not in data_by_table:
                    data_by_table[table_name] = []

                # 添加数据行
                data_by_table[table_name].append(config['values'])

    # 打印统计
    print(f"\n解析完成:")
    total_docs = 0
    for table in sorted(data_by_table.keys()):
        count = len(data_by_table[table])
        total_docs += count
        print(f"  - {table:<30} : {count:>4} 条文档")
    print(f"  - 总计: {total_docs} 条文档")

    # 对每个表的记录进行升序排序
    for table_name in data_by_table:
        data_by_table[table_name] = sort_records(data_by_table[table_name])

    # 重新计算总数（排序后不变）
    total_docs = sum(len(records) for records in data_by_table.values())

    # 生成JSON结构 - 每个表一个键
    json_structure = {
        "metadata": {
            "source_file": os.path.basename(input_file),
            "conversion_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_documents": total_docs,
            "tables": list(data_by_table.keys())
        },
        "data": data_by_table
    }

    # 写入JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_structure, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] JSON文件已生成: {output_file}")
    print(f"   总文档数: {total_docs}")
    print(f"   表数: {len(data_by_table)}")

    # 打印使用说明
    print("\nMongoDB导入示例:")
    print(f"  # 导入单个表（如SCTP）:")
    print(f"  mongoimport --db yourdb --collection SCTP --file {os.path.basename(output_file)} --jsonArray --table=SCTP")
    print(f"  # 注意：需要从JSON文件中提取对应表的数据，或使用脚本预处理")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='MML配置文件转MongoDB JSON格式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法
  python convert_to_mongodb_json.py input.txt

  # 指定输出文件
  python convert_to_mongodb_json.py input.txt -o output.json

  # 指定文件编码（默认gbk）
  python convert_to_mongodb_json.py input.txt --encoding utf-8
        """
    )

    parser.add_argument('input_file', nargs='?', help='输入的MML配置文件路径')
    parser.add_argument('-o', '--output', help='输出的JSON文件路径（默认：同名.json）')
    parser.add_argument('--encoding', default='gbk', help='文件编码（默认：gbk）')

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

    output_json = args.output if args.output else os.path.join(input_dir, f"{input_name}.json")

    print("=" * 60)
    print("MML配置文件转MongoDB JSON格式")
    print("=" * 60)
    print(f"\n输入文件: {args.input_file}")
    print(f"输出JSON: {output_json}")
    print(f"编码: {args.encoding}")
    print()

    try:
        convert_file_to_json(args.input_file, output_json, args.encoding)

        print("\n" + "=" * 60)
        print("转换完成!")
        print("=" * 60)
        print(f"\n生成的文件: {output_json}")
        print("\n导入MongoDB的方法:")
        print("1. 提取单个表数据并导入:")
        print("   jq '.data.SCTP' output.json | mongoimport --db dbname --collection SCTP --jsonArray")
        print("2. 或使用脚本读取JSON并逐文档导入")
    except Exception as e:
        print(f"\n[ERROR] 错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()