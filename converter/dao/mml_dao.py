# -*- coding: utf-8 -*-
"""
数据访问层 (DAO)
所有 SQLite 数据库操作集中在此。
"""

import os
import sqlite3
import json
from typing import Dict, List, Optional, Tuple, Any

from config import get_settings
from converters.mml_to_sql import generate_create_table_sql, generate_insert_sql, infer_column_type

_DB_PATH: str | None = None


def get_db_path() -> str:
    global _DB_PATH
    if _DB_PATH is None:
        _DB_PATH = get_settings()["database"]["path"]
    return _DB_PATH


class DatabaseConnection:
    """数据库连接上下文管理器"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or get_db_path()
        self.conn = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        # 每次会话设置 pragma
        self.conn.execute("PRAGMA foreign_keys = OFF;")
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.conn.close()


# ============================================================
#  元数据操作
# ============================================================


def init_db(db_path: str = None) -> str:
    """初始化数据库：创建元数据表"""
    path = db_path or get_db_path()
    with DatabaseConnection(db_path=path) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS _mml_meta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL UNIQUE,
                columns_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    return f"[OK] 数据库已初始化: {get_db_path()}"


def get_all_meta_tables() -> List[Dict]:
    """获取所有 MML 表的元数据"""
    with DatabaseConnection() as db:
        cursor = db.execute("SELECT * FROM _mml_meta ORDER BY table_name")
        return [dict(row) for row in cursor.fetchall()]


def get_table_meta(table_name: str) -> Optional[Dict]:
    """获取单个表的元数据"""
    with DatabaseConnection() as db:
        cursor = db.execute("SELECT * FROM _mml_meta WHERE table_name = ?", (table_name,))
        row = cursor.fetchone()
        return dict(row) if row else None


def upsert_meta(table_name: str, columns: List[str]) -> None:
    """创建或更新元数据记录"""
    columns_json = json.dumps(columns, ensure_ascii=False)
    with DatabaseConnection() as db:
        db.execute(
            """
            INSERT INTO _mml_meta (table_name, columns_json)
            VALUES (?, ?)
            ON CONFLICT(table_name) DO UPDATE SET
                columns_json = ?,
                updated_at = CURRENT_TIMESTAMP
        """,
            (table_name, columns_json, columns_json),
        )


# ============================================================
#  动态表操作
# ============================================================


def _get_existing_columns(db, table_name: str) -> set:
    """获取表当前已有的列名"""
    cursor = db.execute(f'PRAGMA table_info("{table_name}")')
    return {row["name"] for row in cursor.fetchall()}


def ensure_columns(table_name: str, required_columns: List[str]) -> List[str]:
    """
    确保表拥有所有需要的列，缺少的自动 ALTER TABLE ADD COLUMN。
    返回该表的完整列名列表。
    """
    with DatabaseConnection() as db:
        existing = _get_existing_columns(db, table_name)
        all_cols = sorted(existing | set(required_columns))

        for col in required_columns:
            if col not in existing:
                col_type = infer_column_type(col)
                try:
                    db.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "{col}" {col_type}')
                except Exception as e:
                    print(f"[WARN] 添加列 {table_name}.{col} 失败: {e}")

        return all_cols


def create_table_if_not_exists(table_name: str, columns: List[str]) -> bool:
    """创建表（如已存在则什么都不做）"""
    sql = generate_create_table_sql(table_name, columns)
    with DatabaseConnection() as db:
        try:
            db.execute(sql)
            return True
        except Exception:
            return False


def count_rows(table_name: str) -> int:
    """获取表的总行数"""
    with DatabaseConnection() as db:
        cursor = db.execute(f'SELECT COUNT(*) as cnt FROM "{table_name}"')
        return cursor.fetchone()["cnt"]


def insert_row(table_name: str, data: Dict[str, Any]) -> int:
    """
    插入一行数据。
    返回新行的 rowid。
    """
    sql, values = generate_insert_sql(table_name, data, for_sql_file=False)
    with DatabaseConnection() as db:
        cursor = db.execute(sql, values)
        return cursor.lastrowid


def update_row(table_name: str, rowid: int, data: Dict[str, Any]) -> bool:
    """更新一行数据，返回是否更新成功"""
    set_parts = []
    values = []
    for key, val in data.items():
        set_parts.append(f'"{key}" = ?')
        values.append(val)
    if not set_parts:
        return False

    values.append(rowid)
    set_clause = ", ".join(set_parts)
    with DatabaseConnection() as db:
        cursor = db.execute(f'UPDATE "{table_name}" SET {set_clause} WHERE rowid = ?', values)
        return cursor.rowcount > 0


def delete_row(table_name: str, rowid: int) -> bool:
    """删除一行数据，返回是否删除成功"""
    with DatabaseConnection() as db:
        cursor = db.execute(f'DELETE FROM "{table_name}" WHERE rowid = ?', (rowid,))
        return cursor.rowcount > 0


def delete_rows(table_name: str, rowids: List[int]) -> int:
    """批量删除多行数据，返回删除的行数"""
    if not rowids:
        return 0
    placeholders = ",".join(["?"] * len(rowids))
    with DatabaseConnection() as db:
        cursor = db.execute(f'DELETE FROM "{table_name}" WHERE rowid IN ({placeholders})', rowids)
        return cursor.rowcount


def query_rows(
    table_name: str,
    columns: List[str],
    page: int = 1,
    page_size: int = 20,
    sort_by: str = None,
    sort_order: str = "asc",
) -> Tuple[List[Dict], int]:
    """
    分页查询。
    返回 (rows, total_count)。
    每行包含 rowid 和所有列的值。
    """
    cols_quoted = [f'"{c}"' for c in columns]
    cols_str = ", ".join(cols_quoted)
    offset = (page - 1) * page_size

    # 排序
    if sort_by and sort_by in columns:
        sort_col = f'"{sort_by}"'
        order = "ASC" if sort_order.lower() == "asc" else "DESC"
        order_clause = f"ORDER BY {sort_col} {order}"
    else:
        order_clause = "ORDER BY rowid"

    with DatabaseConnection() as db:
        # 总行数
        total = db.execute(f'SELECT COUNT(*) as cnt FROM "{table_name}"').fetchone()["cnt"]

        # 分页数据
        cursor = db.execute(
            f'SELECT rowid, {cols_str} FROM "{table_name}" {order_clause} LIMIT ? OFFSET ?', (page_size, offset)
        )
        rows = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            config_data = {col: row_dict.get(col) for col in columns}
            rows.append(
                {
                    "id": row_dict["rowid"],
                    "config_data": config_data,
                }
            )

        return rows, total


def query_row(table_name: str, rowid: int, columns: List[str]) -> Optional[Dict]:
    """查询单行数据"""
    cols_quoted = [f'"{c}"' for c in columns]
    cols_str = ", ".join(cols_quoted)

    with DatabaseConnection() as db:
        cursor = db.execute(f'SELECT rowid, {cols_str} FROM "{table_name}" WHERE rowid = ?', (rowid,))
        row = cursor.fetchone()
        if not row:
            return None

        row_dict = dict(row)
        config_data = {col: row_dict.get(col) for col in columns}
        return {
            "id": row_dict["rowid"],
            "config_data": config_data,
        }


def query_all_rows(table_name: str, columns: List[str]) -> List[Dict]:
    """查询表的所有行（用于导出）"""
    cols_quoted = [f'"{c}"' for c in columns]
    cols_str = ", ".join(cols_quoted)

    with DatabaseConnection() as db:
        cursor = db.execute(f'SELECT {cols_str} FROM "{table_name}" ORDER BY rowid')
        return [dict(row) for row in cursor.fetchall()]


def query_rows_by_ids(table_name: str, rowids: List[int], columns: List[str]) -> List[Dict]:
    """按 rowid 列表查询多行数据"""
    if not rowids:
        return []
    cols_quoted = [f'"{c}"' for c in columns]
    cols_str = ", ".join(cols_quoted)
    placeholders = ",".join(["?"] * len(rowids))

    with DatabaseConnection() as db:
        cursor = db.execute(
            f'SELECT rowid, {cols_str} FROM "{table_name}" WHERE rowid IN ({placeholders}) ORDER BY rowid', rowids
        )
        return [dict(row) for row in cursor.fetchall()]
