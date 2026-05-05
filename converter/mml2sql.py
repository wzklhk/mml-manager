#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MML配置文件转SQLite SQL脚本
支持命令行参数指定输入文件
"""
import re
import sqlite3
from datetime import datetime
from typing import List, Dict, Tuple
import os
import argparse


def parse_global_config(line: str) -> Dict[str, str]:
    """解析全局SET配置"""
    match = re.match(r'SET\s+(\w+):(.+)', line.strip())
    if match:
        table_name = match.group(1)  # SCTPGLOBAL
        values_str = match.group(2)
        values = parse_key_value_pairs(values_str)
        return {'table': table_name, 'values': values}
    return None


def parse_sctp_config(line: str) -> Dict[str, str]:
    """解析SCTP ADD配置"""
    match = re.match(r'ADD\s+(\w+):(.+)', line.strip())
    if match:
        table_name = match.group(1)  # SCTP
        values_str = match.group(2)
        values = parse_key_value_pairs(values_str)
        return {'table': table_name, 'values': values}
    return None


def parse_key_value_pairs(text: str) -> Dict[str, str]:
    """解析键值对，如 ID=201,NAME="ToJSZUSPP01_SCTP_SYN_01",LOCPORT=5001"""
    result = {}
    # 使用正则匹配 KEY=VALUE 或 KEY="value" 格式
    pattern = r'(\w+)=(?:"([^"]*)"|([^,]*))'
    matches = re.findall(pattern, text)

    for key, quoted_val, unquoted_val in matches:
        value = quoted_val if quoted_val else unquoted_val
        value = value.strip()
        # Convert empty strings to None to represent NULL in SQL, preventing type mismatches
        if value == '':
            result[key] = None
        else:
            result[key] = value

    return result


def generate_create_table_sql(table_name: str, columns: List[str], include_timestamp: bool = False) -> str:
    """生成CREATE TABLE语句，对所有列名加双引号以避免SQLite关键字冲突

    Args:
        table_name: 表名
        columns: 列名列表
        include_timestamp: 是否包含import_timestamp列（已废弃，始终不包含）
    """
    columns_sql = []
    for col in columns:
        col_type = infer_column_type(col)
        # 给列名加上双引号
        col_safe = f'"{col}"'
        columns_sql.append(f"{col_safe} {col_type}")
    columns_str = ",\n  ".join(columns_sql)

    # 始终不包含 import_timestamp
    return f"CREATE TABLE IF NOT EXISTS {table_name} (\n  {columns_str}\n);"


def infer_column_type(column_name: str) -> str:
    """根据列名推断SQLite数据类型"""
    # ID相关的通常是整数
    if column_name.endswith('ID') or column_name in ['LOCPORT', 'REMPORT', 'INSTRM', 'OUTSTRM',
                                                     'MAXRTRY', 'MAXRTO', 'MINRTO', 'INITRTO',
                                                     'QOSVALUE', 'HB', 'SCTPMAXRTRYNUM', 'DELAYACK',
                                                     'PMTU', 'CB', 'MINCWND', 'PLTIMER', 'MPPLTHRD',
                                                     'OFCID', 'MPDTHRD', 'DTLSCERTID', 'CDBTENANTID',
                                                     'STATASSOFULLTHR', 'REBALANCECPUTHRESH', 'REBALANCEINTERVAL',
                                                     'REBALANCEFORBIDTIME', 'SCRECOVERYTIMERLEN', 'SCTPDYNAINITLIMIT',
                                                     'SCTPDYNALARMLIMIT']:
        return "INTEGER"
    # 数值相关的可能是整数或浮点数
    elif column_name in ['SCTPTXNOTIFYTHRESH']:
        return "INTEGER"
    # 其他可能是字符串
    else:
        return "TEXT"


def generate_insert_sql(table_name: str, data: Dict[str, str], include_timestamp: bool = False,
                        import_timestamp: str = None, for_sql_file: bool = False) -> Tuple[str, List]:
    """生成INSERT语句，给列名加引号以避免关键字冲突

    Args:
        table_name: 表名
        data: 数据字典
        include_timestamp: 是否包含import_timestamp列（已废弃，始终不包含）
        import_timestamp: 时间戳字符串（已废弃）
        for_sql_file: 是否为生成SQL文件（True则直接拼接值，False则使用占位符返回values）
    """
    columns = list(data.keys())
    values = list(data.values())

    # 不再添加 import_timestamp 列

    # 给列名加双引号
    columns_quoted = [f'"{col}"' for col in columns]
    columns_str = ', '.join(columns_quoted)

    if for_sql_file:
        # 直接拼接值，生成完整的SQL语句
        values_sql = []
        for v in values:
            if v is None:
                values_sql.append('NULL')
            elif isinstance(v, (int, float)):
                values_sql.append(str(v))
            else:
                # 转义单引号，并用单引号包裹字符串
                v_escaped = str(v).replace("'", "''")
                values_sql.append(f"'{v_escaped}'")
        values_str = ', '.join(values_sql)
        sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});"
        return sql, []  # 空values列表，因为不需要参数化
    else:
        # 为数据库准备参数化查询（占位符+values）
        placeholders = ['?'] * len(columns)
        placeholders_str = ', '.join(placeholders)
        sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders_str});"
        return sql, values


def convert_file_to_sql(input_file: str, output_file: str, db_name: str = None, encoding: str = 'utf-8'):
    """
    转换配置文件为SQL

    Args:
        input_file: 输入文件路径
        output_file: 输出SQL文件路径
        db_name: 数据库文件名（用于创建数据库）
        encoding: 文件编码
    """
    print(f"正在读取文件: {input_file}")

    with open(input_file, 'r', encoding=encoding) as f:
        lines = f.readlines()

    # 统计数据 - 支持所有MML命令类型
    configs_by_table = {}  # table_name -> list of config dicts
    all_columns = {}  # table_name -> set of columns

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('--'):
            continue

        if line.startswith('ENTER'):
            # 记录配置段开始（忽略）
            continue

        elif line.startswith('SET') or line.startswith('ADD'):
            config = parse_any_command(line)
            if config:
                table_name = config['table']
                if table_name not in configs_by_table:
                    configs_by_table[table_name] = []
                    all_columns[table_name] = set()

                configs_by_table[table_name].append(config)
                all_columns[table_name].update(config['values'].keys())

                # DEBUG: 打印第一个解析的配置值
                if line_num <= 5:
                    print(f"[DEBUG] Line {line_num}: table={table_name}, values={config['values']}", flush=True)

    # 打印解析统计
    print(f"\n解析完成:")
    total_configs = 0
    for table in sorted(configs_by_table.keys()):
        count = len(configs_by_table[table])
        total_configs += count
        print(f"  - {table:<30} : {count:>4} 条")
    print(f"  - 总计: {total_configs} 条配置")

    # 对每个表的记录进行升序排序
    for table_name in configs_by_table:
        configs_by_table[table_name] = sort_configs_by_values(configs_by_table[table_name])

    print(f"\n已对每个表的记录进行升序排序")

    # 生成SQL
    sql_statements = []

    # 添加SQLite pragmas
    sql_statements.append("-- SQLite配置")
    sql_statements.append("PRAGMA encoding = 'UTF-8';")
    sql_statements.append("PRAGMA foreign_keys = OFF;")
    sql_statements.append("PRAGMA journal_mode = WAL;")
    sql_statements.append("")

    # 为每个表生成CREATE和INSERT语句
    for table_name in sorted(all_columns.keys()):
        columns = sorted(list(all_columns[table_name]))

        # 创建表（不包含import_timestamp列）
        sql_statements.append(f"-- {table_name} 表")
        sql_statements.append(f"DROP TABLE IF EXISTS {table_name};")
        sql_statements.append(generate_create_table_sql(table_name, columns))
        sql_statements.append("")

        # 插入数据（不包含import_timestamp）
        for config in configs_by_table[table_name]:
            insert_sql, _ = generate_insert_sql(table_name, config['values'], for_sql_file=True)
            sql_statements.append(insert_sql)
        sql_statements.append("")

    # 添加通用查询示例
    sql_statements.append("-- 查询示例")
    for table_name in sorted(all_columns.keys()):
        sql_statements.append(f"-- 查看{table_name}表记录数:")
        sql_statements.append(f"-- SELECT COUNT(*) FROM {table_name};")
        sql_statements.append("")

        # 如果有ID列的查询示例
        if 'ID' in all_columns[table_name]:
            sql_statements.append(f"-- 查看{table_name}中ID>100的记录:")
            sql_statements.append(f"-- SELECT * FROM {table_name} WHERE ID > 100 LIMIT 10;")
            sql_statements.append("")

    # 写入SQL文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_statements))

    print(f"\n[OK] SQL文件已生成: {output_file}")
    print(f"   总SQL语句数: {len(sql_statements)}")
    print(f"   数据行数: {sum(len(configs) for configs in configs_by_table.values())}")
    print(f"   数据表数: {len(all_columns)}")

    # 如果指定了数据库名，创建并导入数据库
    if db_name:
        db_path = os.path.join(os.path.dirname(output_file), db_name)
        create_database(db_path, configs_by_table, all_columns)
        print(f"\n✅ SQLite数据库已创建: {db_path}")
        print(f"   可以使用以下命令查看:")
        for table_name in sorted(all_columns.keys())[:3]:  # 只显示前3个表示例
            print(f"   sqlite3 {db_name} 'SELECT COUNT(*) FROM {table_name};'")
        if len(all_columns) > 3:
            print(f"   ... 等共{len(all_columns)}个表")


def parse_any_command(line: str) -> Dict[str, str]:
    """解析任意SET或ADD命令"""
    match = re.match(r'(SET|ADD)\s+(\w+):(.+)', line.strip())
    if match:
        cmd_type = match.group(1)
        table_name = match.group(2)
        values_str = match.group(3)
        
        # 去除末尾的分号，避免将其作为数据的一部分
        if values_str.endswith(';'):
            values_str = values_str[:-1]
            
        values = parse_key_value_pairs(values_str)
        # DEBUG: 打印解析出的表名
        # print(f"[DEBUG] 解析: {cmd_type} {table_name} 列数={len(values)}")
        return {'table': table_name, 'values': values, 'cmd_type': cmd_type}
    # DEBUG: 未匹配的行
    # print(f"[DEBUG] 未匹配: {line[:80]}")
    return None


def sort_configs_by_values(configs: List[Dict]) -> List[Dict]:
    """
    对配置记录列表进行升序排序（基于 values 字段）
    优先按 ID 字段（如果存在），否则按字典的第一个键值对排序
    智能识别数字：如果值全部由数字组成，按数值排序；否则按字符串排序
    """
    if not configs:
        return configs

    def try_parse_int(value: str):
        """尝试解析为整数，失败返回None"""
        if value is None:
            return None
        value = str(value).strip()
        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            try:
                return int(value)
            except ValueError:
                return None
        return None

    def sort_key(config: Dict) -> tuple:
        values = config.get('values', {})
        if not values:
            return (2, 1, '')

        # 检查是否有 ID 或类似主键的字段
        id_fields = ['ID', 'INDEX', 'SEQ', 'SEQUENCE']
        for field in id_fields:
            if field in values:
                val = values[field]
                num = try_parse_int(val)
                if num is not None:
                    return (0, 0, num)  # (优先级, 类型:0数字, 数值)
                else:
                    return (0, 1, str(val))  # (优先级, 类型:1字符串, 字符串值)

        # 没有主键字段，按第一条字段值排序（按字段名字母顺序取第一个）
        first_key = sorted(values.keys())[0]
        val = values[first_key]
        num = try_parse_int(val)
        if num is not None:
            return (1, 0, num)
        else:
            return (1, 1, str(val))

    return sorted(configs, key=sort_key)


def create_database(db_path: str, configs_by_table: Dict, all_columns: Dict):
    """创建SQLite数据库并导入数据（不包含import_timestamp列）"""
    import sys
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 启用外键支持
    cursor.execute("PRAGMA foreign_keys = OFF;")

    # 为每个表创建表结构并插入数据
    for table_name in sorted(all_columns.keys()):
        print(
            f"[DEBUG] 处理表: {table_name}, 列数: {len(all_columns[table_name])}, 数据行: {len(configs_by_table[table_name])}",
            file=sys.stderr)
        columns = sorted(list(all_columns[table_name]))

        # 生成并执行CREATE TABLE语句（不包含import_timestamp）
        create_sql = generate_create_table_sql(table_name, columns, include_timestamp=False)
        print(f"[DEBUG] CREATE SQL: {create_sql[:200]}...", file=sys.stderr)
        try:
            cursor.execute(create_sql)
        except Exception as e:
            print(f"[ERROR] 创建表 {table_name} 失败: {e}", file=sys.stderr)
            conn.rollback()
            raise

        # 插入数据（不包含import_timestamp）
        for i, config in enumerate(configs_by_table[table_name]):
            insert_sql, values = generate_insert_sql(table_name, config['values'], include_timestamp=False,
                                                     for_sql_file=False)
            try:
                cursor.execute(insert_sql, values)
            except Exception as e:
                print(f"[ERROR] 插入表 {table_name} 第{i + 1}行失败: {e}", file=sys.stderr)
                print(f"   SQL: {insert_sql}", file=sys.stderr)
                print(f"   值: {values}", file=sys.stderr)
                raise

    conn.commit()
    conn.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='MML配置文件转SQLite SQL脚本 - 支持所有MML命令',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法（自动生成SQL和DB）
  python convert_to_sqlite.py input.txt

  # 指定输出文件
  python convert_to_sqlite.py input.txt -o output.sql

  # 只生成SQL，不创建数据库
  python convert_to_sqlite.py input.txt --sql-only

  # 指定数据库文件名
  python convert_to_sqlite.py input.txt -d custom.db

  # 查看所有支持的MML命令类型
  python convert_to_sqlite.py --list-commands input.txt
        """
    )

    parser.add_argument('input_file', nargs='?',
                        help='输入的MML配置文件路径')
    parser.add_argument('-o', '--output',
                        help='输出的SQL文件路径（默认：同名.sql）')
    parser.add_argument('-d', '--database',
                        help='SQLite数据库文件名（默认：同名.db）')
    parser.add_argument('--sql-only', action='store_true',
                        help='只生成SQL文件，不创建数据库')
    parser.add_argument('--list-commands', action='store_true',
                        help='列出文件中发现的所有MML命令类型')
    parser.add_argument('--encoding', default='utf-8',
                        help='文件编码（默认：utf-8）')

    args = parser.parse_args()

    # 如果只列出命令类型
    if args.list_commands and args.input_file:
        list_commands_in_file(args.input_file, args.encoding)
        return

    # 如果没有提供输入文件，显示帮助
    if not args.input_file:
        parser.print_help()
        return

    # 检查输入文件是否存在
    if not os.path.exists(args.input_file):
        print(f"❌ 错误: 输入文件不存在!")
        print(f"   路径: {args.input_file}")
        return

    # 确定输出路径
    input_dir = os.path.dirname(os.path.abspath(args.input_file))
    input_name = os.path.splitext(os.path.basename(args.input_file))[0]

    output_sql = args.output if args.output else os.path.join(input_dir, f"{input_name}.sql")
    db_name = args.database if args.database else f"{input_name}.db"

    print("=" * 60)
    print("MML配置文件转SQLite SQL脚本")
    print("=" * 60)
    print(f"\n输入文件: {args.input_file}")
    print(f"输出SQL:  {output_sql}")
    if not args.sql_only:
        print(f"输出数据库: {os.path.join(input_dir, db_name)}")
    print()

    # 转换文件
    try:
        convert_file_to_sql(args.input_file, output_sql, db_name if not args.sql_only else None)

        print("\n" + "=" * 60)
        print("转换完成!")
        print("=" * 60)
        print(f"\n生成的文件:")
        print(f"  1. SQL脚本: {output_sql}")
        if not args.sql_only:
            print(f"  2. SQLite数据库: {os.path.join(input_dir, db_name)}")
        print("\n使用方法:")
        print(f"  1. 直接使用SQL脚本:")
        print(f"     sqlite3 mydb.db < {os.path.basename(output_sql)}")
        if not args.sql_only:
            print(f"  2. 或使用已创建的数据库:")
            print(f"     sqlite3 {db_name} 'SELECT COUNT(*) FROM SCTP;'")
    except Exception as e:
        print(f"\n[ERROR] 错误: {str(e)}")
        import traceback
        traceback.print_exc()


def list_commands_in_file(file_path: str, encoding: str):
    """列出文件中所有的MML命令类型"""
    print("=" * 60)
    print("MML命令类型统计")
    print("=" * 60)
    print(f"\n文件: {file_path}\n")

    command_types = {}
    table_columns = {}

    with open(file_path, 'r', encoding=encoding) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('--'):
                continue

            if line.startswith('SET') or line.startswith('ADD'):
                match = re.match(r'(SET|ADD)\s+(\w+):(.+)', line)
                if match:
                    cmd_type = match.group(1)
                    table_name = match.group(2)
                    key = f"{cmd_type} {table_name}"

                    command_types[key] = command_types.get(key, 0) + 1

                    if table_name not in table_columns:
                        table_columns[table_name] = set()

                    # 解析键值对
                    values_str = match.group(3)
                    values = parse_key_value_pairs(values_str)
                    table_columns[table_name].update(values.keys())

    # 输出统计
    print("命令类型统计:")
    print("-" * 40)
    for cmd, count in sorted(command_types.items()):
        print(f"  {cmd:<30} : {count:>4} 条")

    print("\n检测到的表结构:")
    print("-" * 40)
    for table, columns in sorted(table_columns.items()):
        print(f"\n表名: {table}")
        print(f"  列数: {len(columns)}")
        print(f"  列名: {', '.join(sorted(columns)[:10])}", end='')
        if len(columns) > 10:
            print(f" ... (+{len(columns) - 10} more)")
        else:
            print()


if __name__ == "__main__":
    main()
