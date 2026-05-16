# -*- coding: utf-8 -*-
"""MML → SQL 转换核心模块"""
import os
import re
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ============================================================
#  解析
# ============================================================

def parse_key_value_pairs(text: str) -> Dict[str, Optional[str]]:
    """解析键值对，如 ID=201,NAME="ToJSZUSPP01_SCTP_SYN_01",LOCPORT=5001"""
    result = {}
    pattern = r'(\w+)=(?:"([^"]*)"|([^,]*))'
    for key, quoted_val, unquoted_val in re.findall(pattern, text):
        value = quoted_val if quoted_val else unquoted_val
        value = value.strip()
        result[key] = value if value else None
    return result


def parse_any_command(line: str) -> Optional[Dict]:
    """解析任意 SET 或 ADD 命令"""
    match = re.match(r'(SET|ADD)\s+(\w+):(.+)', line.strip())
    if not match:
        return None
    cmd_type = match.group(1)
    table_name = match.group(2)
    values_str = match.group(3)
    if values_str.endswith(';'):
        values_str = values_str[:-1]
    values = parse_key_value_pairs(values_str)
    return {'table': table_name, 'values': values, 'cmd_type': cmd_type}


# ============================================================
#  类型推断 & SQL 生成
# ============================================================

_INTEGER_COLUMNS = {
    'LOCPORT', 'REMPORT', 'INSTRM', 'OUTSTRM',
    'MAXRTRY', 'MAXRTO', 'MINRTO', 'INITRTO',
    'QOSVALUE', 'HB', 'SCTPMAXRTRYNUM', 'DELAYACK',
    'PMTU', 'CB', 'MINCWND', 'PLTIMER', 'MPPLTHRD',
    'OFCID', 'MPDTHRD', 'DTLSCERTID', 'CDBTENANTID',
    'STATASSOFULLTHR', 'REBALANCECPUTHRESH', 'REBALANCEINTERVAL',
    'REBALANCEFORBIDTIME', 'SCRECOVERYTIMERLEN', 'SCTPDYNAINITLIMIT',
    'SCTPDYNALARMLIMIT', 'SCTPTXNOTIFYTHRESH',
}


def infer_column_type(column_name: str) -> str:
    """根据列名推断 SQLite 数据类型"""
    if column_name.endswith('ID') or column_name in _INTEGER_COLUMNS:
        return "INTEGER"
    return "TEXT"


def generate_create_table_sql(table_name: str, columns: List[str]) -> str:
    """生成 CREATE TABLE IF NOT EXISTS 语句"""
    cols = [f'  "{c}" {infer_column_type(c)}' for c in columns]
    nl = "\n"
    sep = ",\n"
    return f"CREATE TABLE IF NOT EXISTS {table_name} ({nl}{sep.join(cols)}{nl});"


def generate_insert_sql(
    table_name: str, data: Dict[str, str],
    for_sql_file: bool = False,
) -> Tuple[str, List]:
    """生成 INSERT 语句。

    Args:
        table_name: 表名
        data: 数据字典
        for_sql_file: True 则直接拼接值，False 则用 ? 占位符

    Returns:
        (sql, values)
    """
    columns = list(data.keys())
    values = list(data.values())
    cols_quoted = [f'"{c}"' for c in columns]
    cols_str = ', '.join(cols_quoted)

    if for_sql_file:
        quote = chr(39)
        vals = []
        for v in values:
            if v is None:
                vals.append('NULL')
            elif isinstance(v, (int, float)):
                vals.append(str(v))
            else:
                escaped = str(v).replace(quote, quote + quote)
                vals.append(f"{quote}{escaped}{quote}")
        sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({', '.join(vals)});"
        return sql, []
    else:
        placeholders = ', '.join(['?'] * len(columns))
        sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders});"
        return sql, values


# ============================================================
#  排序
# ============================================================

def sort_configs_by_values(configs: List[Dict]) -> List[Dict]:
    """按 values 字段对配置排序，优先 ID 字段"""
    def _try_parse_int(v):
        if v is None:
            return None
        s = str(v).strip()
        if s.isdigit() or (s.startswith('-') and s[1:].isdigit()):
            try:
                return int(s)
            except ValueError:
                pass
        return None

    def _sort_key(config):
        vals = config.get('values', {})
        if not vals:
            return (2, 1, '')
        for field in ['ID', 'INDEX', 'SEQ', 'SEQUENCE']:
            if field in vals:
                n = _try_parse_int(vals[field])
                return (0, 0, n) if n is not None else (0, 1, str(vals[field]))
        first_key = sorted(vals.keys())[0]
        n = _try_parse_int(vals[first_key])
        return (1, 0, n) if n is not None else (1, 1, str(vals[first_key]))

    return sorted(configs, key=_sort_key)


# ============================================================
#  文件 → SQL / 数据库
# ============================================================

def parse_mml_file(input_path: str, encoding: str = 'utf-8') -> Tuple[Dict, Dict]:
    """解析 MML 文件，返回 (configs_by_table, all_columns)"""
    configs_by_table = {}
    all_columns = {}

    with open(input_path, 'r', encoding=encoding) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            config = parse_any_command(line)
            if config:
                tn = config['table']
                if tn not in configs_by_table:
                    configs_by_table[tn] = []
                    all_columns[tn] = set()
                configs_by_table[tn].append(config)
                all_columns[tn].update(config['values'].keys())

    for tn in configs_by_table:
        configs_by_table[tn] = sort_configs_by_values(configs_by_table[tn])

    return configs_by_table, all_columns


def generate_sql_script(
    configs_by_table: Dict, all_columns: Dict,
    include_comments: bool = True,
) -> List[str]:
    """生成 SQL 脚本语句列表"""
    statements = []
    if include_comments:
        statements.append("-- SQLite 配置")
        statements.append("PRAGMA encoding = 'UTF-8';")
        statements.append("PRAGMA foreign_keys = OFF;")
        statements.append("PRAGMA journal_mode = WAL;")
        statements.append("")

    for table_name in sorted(all_columns.keys()):
        columns = sorted(list(all_columns[table_name]))
        if include_comments:
            statements.append(f"-- {table_name} 表")
        statements.append(f"DROP TABLE IF EXISTS {table_name};")
        statements.append(generate_create_table_sql(table_name, columns))
        statements.append("")

        for config in configs_by_table[table_name]:
            sql, _ = generate_insert_sql(table_name, config['values'], for_sql_file=True)
            statements.append(sql)
        statements.append("")

    if include_comments:
        statements.append("-- 查询示例")
        for tn in sorted(all_columns.keys()):
            statements.append(f"-- SELECT COUNT(*) FROM {tn};")
            if 'ID' in all_columns[tn]:
                statements.append(f"-- SELECT * FROM {tn} WHERE ID > 100 LIMIT 10;")
            statements.append("")

    return statements


def convert_file_to_sql(
    input_file: str, output_file: str,
    db_name: str = None, encoding: str = 'utf-8',
) -> Tuple[int, int]:
    """转换 MML 文件为 SQL 脚本。

    Returns:
        (config_count, table_count)
    """
    configs_by_table, all_columns = parse_mml_file(input_file, encoding)
    total = sum(len(v) for v in configs_by_table.values())

    statements = generate_sql_script(configs_by_table, all_columns)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(statements))

    if db_name:
        output_dir = os.path.dirname(output_file)
        db_path = os.path.join(output_dir, db_name)
        create_database(db_path, configs_by_table, all_columns)

    return total, len(all_columns)


def create_database(db_path: str, configs_by_table: Dict, all_columns: Dict):
    """创建 SQLite 数据库并导入数据"""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = OFF;")

    for table_name in sorted(all_columns.keys()):
        columns = sorted(list(all_columns[table_name]))
        conn.execute(f"DROP TABLE IF EXISTS {table_name};")
        conn.execute(generate_create_table_sql(table_name, columns))

        for config in configs_by_table[table_name]:
            sql, values = generate_insert_sql(table_name, config['values'], for_sql_file=False)
            conn.execute(sql, values)

    conn.commit()
    conn.close()


def list_commands_in_file(file_path: str, encoding: str = 'utf-8') -> Dict:
    """列出文件中所有命令类型和列统计"""
    command_types = {}
    table_columns = {}

    with open(file_path, 'r', encoding=encoding) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            config = parse_any_command(line)
            if config:
                key = f"{config['cmd_type']} {config['table']}"
                command_types[key] = command_types.get(key, 0) + 1
                tn = config['table']
                if tn not in table_columns:
                    table_columns[tn] = set()
                table_columns[tn].update(config['values'].keys())

    return {'command_types': command_types, 'table_columns': table_columns}
