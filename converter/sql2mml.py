#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL转MML配置命令脚本

支持从SQL INSERT语句或SELECT查询结果表格文本中解析数据，
并转换为MML配置命令格式。也支持数据库直连模式。

用法:
  # INSERT语句解析（自动检测）
  python sql2mml.py data.sql

  # SELECT结果表格解析
  python sql2mml.py data.sql --format select

  # 指定表名
  python sql2mml.py data.sql --table LTE_CELL

  # 数据库直连模式 - MySQL
  python sql2mml.py --db mysql --db-host 10.0.0.1 ...
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import Dict, List, Optional
from datetime import datetime

from cli_common import (
    add_input_output_args, add_cmd_type_arg,
    resolve_output_path, check_file_exists,
)
from utils.io_handler import (
    write_mml_file, print_statistics, print_banner, print_footer
)
from utils.table import MmlDataSet, MmlConfig, sanitize_table_name
from utils.mml import quote_mml_value


# ============================================================
#  INSERT语句解析
# ============================================================

def parse_insert_statements(sql_text: str) -> List[Dict]:
    """
    从SQL文本中解析INSERT语句。

    支持: INSERT INTO table (col1, col2) VALUES (val1, val2), (val3, val4);
          INSERT table SET col1=val1, col2=val2;

    Returns:
        [{'table': str, 'columns': [str], 'values': [str]}, ...]
    """
    results = []

    pattern = re.compile(
        r'INSERT\s+(?:INTO\s+)?(\w+)\s*'
        r'\(([^)]+)\)\s*VALUES\s*'
        r'(\([^)]+\)(?:\s*,\s*\([^)]+\))*)',
        re.IGNORECASE | re.DOTALL
    )

    for match in pattern.finditer(sql_text):
        table_name = match.group(1).strip()
        columns = [c.strip().strip('`"\'') for c in match.group(2).split(',')]
        values_block = match.group(3)

        for value_set in _parse_value_tuples(values_block):
            if len(value_set) == len(columns):
                results.append({
                    'table': table_name,
                    'columns': columns,
                    'values': value_set,
                })

    return results


def _parse_value_tuples(values_block: str) -> List[List[str]]:
    """解析VALUES值元组列表"""
    tuples = []
    current_tuple = []
    current_val = []
    depth = 0
    in_quote = False
    quote_char = None

    for ch in values_block:
        if in_quote:
            if ch == quote_char:
                in_quote = False
            current_val.append(ch)
        elif ch in ("'", '"'):
            in_quote = True
            quote_char = ch
            current_val.append(ch)
        elif ch == '(':
            if depth > 0:
                current_val.append(ch)
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                current_tuple.append(''.join(current_val).strip())
                current_val = []
                tuples.append(current_tuple)
                current_tuple = []
            else:
                current_val.append(ch)
        elif ch == ',' and depth == 1:
            current_tuple.append(''.join(current_val).strip())
            current_val = []
        elif depth >= 1:
            current_val.append(ch)

    return tuples


# ============================================================
#  SELECT结果表格解析
# ============================================================

def parse_select_result(sql_text: str) -> List[Dict]:
    """
    从SELECT查询结果文本（+---+ 表格格式）中解析数据。

    Returns:
        [{'table': str, 'columns': [str], 'values': [str]}, ...]
    """
    lines = sql_text.strip().split('\n')
    results = []

    sep_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('+') and '-' in line:
            sep_idx = i
            break

    if sep_idx < 0 or sep_idx + 2 >= len(lines):
        return results

    if not lines[sep_idx + 1].strip().startswith('|'):
        return results

    headers = _parse_table_row(lines[sep_idx + 1])
    if not headers:
        return results

    next_sep = -1
    for i in range(sep_idx + 2, len(lines)):
        if lines[i].strip().startswith('+'):
            next_sep = i
            break

    if next_sep < 0:
        return results

    table_name = None
    for i in range(next_sep + 1, len(lines)):
        line = lines[i].strip()
        if not line or line.startswith('+'):
            continue
        if not line.startswith('|'):
            continue
        values = _parse_table_row(line)
        if values and len(values) == len(headers):
            if table_name is None:
                from_match = re.search(r'FROM\s+(\w+)', sql_text, re.IGNORECASE)
                if from_match:
                    table_name = from_match.group(1)
            results.append({
                'table': table_name or 'QUERY_RESULT',
                'columns': headers,
                'values': values,
            })

    return results


def _parse_table_row(line: str) -> List[str]:
    """解析表格行 | id | name | → ['id', 'name']"""
    parts = [p.strip() for p in line.strip().split('|') if p.strip() != '']
    return parts


# ============================================================
#  数据库直连
# ============================================================

def _query_mysql(host, port, user, password, database, query, table_name) -> List[Dict]:
    """直连MySQL查询"""
    try:
        import pymysql
    except ImportError:
        print("❌ 需要安装 pymysql: pip install pymysql")
        return []

    results = []
    try:
        conn = pymysql.connect(host=host, port=port, user=user,
                               password=password, database=database, charset='utf8mb4')
        with conn.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                results.append({
                    'table': table_name,
                    'columns': columns,
                    'values': [str(v) if v is not None else '' for v in row],
                })
        conn.close()
        print(f"[OK] MySQL查询到 {len(results)} 条记录")
    except Exception as e:
        print(f"❌ MySQL查询失败: {e}")
    return results


def _query_mongo(host, port, database, collection, query, table_name) -> List[Dict]:
    """直连MongoDB查询"""
    try:
        from pymongo import MongoClient
    except ImportError:
        print("❌ 需要安装 pymongo: pip install pymongo")
        return []

    results = []
    try:
        client = MongoClient(host, port)
        col = client[database][collection]
        filter_doc = {}
        if query.strip():
            import json
            try:
                filter_doc = json.loads(query)
            except json.JSONDecodeError:
                print("⚠️ MongoDB查询条件非合法JSON，查询全部")

        for doc in col.find(filter_doc).limit(10000):
            flat = {}
            for k, v in doc.items():
                if k == '_id':
                    flat['_id'] = str(v)
                elif isinstance(v, (str, int, float, bool)):
                    flat[k] = str(v)
                elif v is None:
                    flat[k] = ''
                else:
                    flat[k] = str(v)
            results.append({
                'table': table_name,
                'columns': list(flat.keys()),
                'values': list(flat.values()),
            })
        client.close()
        print(f"[OK] MongoDB查询到 {len(results)} 条记录")
    except Exception as e:
        print(f"❌ MongoDB查询失败: {e}")
    return results


# ============================================================
#  核心转换
# ============================================================

def sql_data_to_dataset(data: List[Dict], cmd_type: str = 'SET',
                        default_table: Optional[str] = None) -> MmlDataSet:
    """
    将SQL解析数据转换为MML数据集。

    Args:
        data: SQL解析数据列表
        cmd_type: 命令类型
        default_table: 默认表名

    Returns:
        MmlDataSet
    """
    dataset = MmlDataSet()
    for item in data:
        table = item.get('table') or default_table or 'TABLE'
        columns = item.get('columns', [])
        values_raw = item.get('values', [])

        kv = {}
        for i, col in enumerate(columns):
            val = values_raw[i] if i < len(values_raw) else ''
            qv = quote_mml_value(val)
            if qv:
                kv[col] = qv

        if kv:
            dataset.add(MmlConfig(cmd_type=cmd_type, table=table, values=kv))

    return dataset


def convert_sql_file(input_path: str, output_path: str,
                     cmd_type: str = 'SET', parse_mode: str = 'auto',
                     default_table: Optional[str] = None):
    """从SQL文件解析并转换为MML"""
    print(f"正在读取SQL文件: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    data = []
    if parse_mode in ('auto', 'insert'):
        data = parse_insert_statements(content)
    if not data and parse_mode in ('auto', 'select'):
        data = parse_select_result(content)

    if not data:
        print("⚠️ 未能从文件中解析出有效数据")
        print("   - 确认文件包含 INSERT 语句或 SELECT 结果表格")
        print("   - 尝试用 --format insert 或 --format select")
        return

    print(f"\n解析完成:")
    dataset = sql_data_to_dataset(data, cmd_type=cmd_type, default_table=default_table)
    print_statistics(dataset)
    write_mml_file(output_path, dataset,
                   source_desc="sql2mml.py",
                   cmd_type=cmd_type)


def connect_db_and_convert(args):
    """连接数据库查询并转换"""
    print("数据库直连模式")
    print(f"  - 类型: {args.db_type}")
    print(f"  - 主机: {args.db_host}:{args.db_port}")
    print(f"  - 数据库: {args.database}\n")

    query = args.query or f"SELECT * FROM {args.table}"

    if args.db_type == 'mysql':
        data = _query_mysql(args.db_host, args.db_port, args.db_user,
                            args.db_password, args.database, query, args.table)
    elif args.db_type == 'mongo':
        data = _query_mongo(args.db_host, args.db_port, args.database,
                            args.table, args.query or '', args.table)
    else:
        print(f"❌ 不支持的数据库类型: {args.db_type}")
        return

    if data:
        output_path = args.output or f"{args.table}.mml"
        dataset = sql_data_to_dataset(data, cmd_type=args.cmd)
        print(f"\n转换完成:")
        print_statistics(dataset)
        write_mml_file(output_path, dataset,
                       source_desc="sql2mml.py (数据库直连)",
                       cmd_type=args.cmd)
    else:
        print("⚠️ 未查询到数据")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='SQL转MML配置命令脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # SQL文件转MML（自动检测INSERT/SELECT）
  python sql2mml.py data.sql

  # 指定解析模式
  python sql2mml.py data.sql --format insert
  python sql2mml.py data.sql --format select

  # 指定表名
  python sql2mml.py data.sql --table LTE_CELL

  # 数据库直连 - MySQL
  python sql2mml.py --db mysql --db-host 192.168.1.100 \\
      --db-user root --db-password pass --database omc --table LTE_CELL

  # 数据库直连 - MongoDB
  python sql2mml.py --db mongo --db-host 192.168.1.100 \\
      --database omc --table cell_config
        """
    )

    add_input_output_args(parser,
                          input_help='输入的SQL文件路径（不提供则数据库直连模式）',
                          output_help='输出的MML文件路径',
                          require_input=False)
    add_cmd_type_arg(parser)
    parser.add_argument('--table', help='目标表名（默认自动检测或使用文件名）')
    parser.add_argument('--format', dest='parse_mode', default='auto',
                        choices=['auto', 'insert', 'select'],
                        help='解析模式: auto(默认), insert(INSERT语句), select(查询结果表格)')

    # 数据库直连参数
    parser.add_argument('--db', dest='db_type', choices=['mysql', 'mongo'],
                        help='数据库类型')
    parser.add_argument('--db-host', default='localhost', help='数据库主机')
    parser.add_argument('--db-port', type=int, default=3306,
                        help='端口（MySQL默认3306，MongoDB默认27017）')
    parser.add_argument('--db-user', default='root', help='数据库用户')
    parser.add_argument('--db-password', default='', help='数据库密码')
    parser.add_argument('--database', help='数据库名')
    parser.add_argument('--query', help='自定义SQL查询语句')

    args = parser.parse_args()

    if args.db_type:
        # 数据库直连模式
        if not all([args.database, args.table or args.query]):
            print("❌ 数据库直连模式需要 --database 和 --table（或 --query）")
            return
        if args.db_port == 3306 and args.db_type == 'mongo':
            args.db_port = 27017
        print_banner("SQL转MML - 数据库直连模式",
                     数据库类型=args.db_type,
                     数据库=args.database,
                     命令类型=args.cmd)
        connect_db_and_convert(args)
        print_footer()
        return

    # 文件模式
    if not args.input_file:
        parser.print_help()
        return
    if not check_file_exists(args.input_file):
        return

    default_table = args.table or sanitize_table_name(
        os.path.splitext(os.path.basename(args.input_file))[0]
    )
    output_path = resolve_output_path(args.input_file, args.output)

    print_banner("SQL转MML配置命令",
                 输入文件=args.input_file,
                 输出文件=output_path,
                 解析模式=args.parse_mode,
                 命令类型=args.cmd)

    convert_sql_file(args.input_file, output_path,
                     cmd_type=args.cmd, parse_mode=args.parse_mode,
                     default_table=default_table)
    print_footer()


if __name__ == '__main__':
    main()
