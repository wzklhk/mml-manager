# -*- coding: utf-8 -*-
"""
数据访问层 (DAO)
所有 SQLite 数据库操作集中在此。
"""

import os
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from ..core.config import get_settings
from ..converters.mml_to_sql import generate_create_table_sql, generate_insert_sql, infer_column_type, quote_identifier

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
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        # 每次会话设置 pragma
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.execute("PRAGMA busy_timeout = 5000;")
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
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS _mml_meta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL UNIQUE,
                columns_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
    return f"[OK] 数据库已初始化: {get_db_path()}"


# ============================================================
#  Configuration-set persistence
# ============================================================


def init_snapshot_schema(db_path: str = None) -> None:
    """Create the normalized schema used by the web application's imports."""
    with DatabaseConnection(db_path=db_path) as db:
        db.execute("PRAGMA journal_mode = WAL;")
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS _mml_snapshots (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                network_element TEXT NOT NULL,
                loaded_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS _mml_snapshot_tables (
                snapshot_id TEXT NOT NULL,
                table_name TEXT NOT NULL,
                columns_json TEXT NOT NULL,
                row_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (snapshot_id, table_name),
                FOREIGN KEY (snapshot_id) REFERENCES _mml_snapshots(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS _mml_snapshot_rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id TEXT NOT NULL,
                table_name TEXT NOT NULL,
                cmd_type TEXT NOT NULL,
                values_json TEXT NOT NULL,
                FOREIGN KEY (snapshot_id, table_name)
                    REFERENCES _mml_snapshot_tables(snapshot_id, table_name) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS _idx_mml_rows_snapshot_table
                ON _mml_snapshot_rows(snapshot_id, table_name, id);
            CREATE TABLE IF NOT EXISTS _mml_state (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )


def insert_snapshot(snapshot_id: str, name: str, network_element: str, loaded_at: str, tables: Dict) -> None:
    """Atomically persist one import in batches and make it active."""
    init_snapshot_schema()
    with DatabaseConnection() as db:
        db.execute(
            "INSERT INTO _mml_snapshots(id, name, network_element, loaded_at) VALUES (?, ?, ?, ?)",
            (snapshot_id, name, network_element, loaded_at),
        )
        for table_name, commands in tables.items():
            columns = sorted({key for command in commands for key in command["values"]})
            db.execute(
                "INSERT INTO _mml_snapshot_tables(snapshot_id, table_name, columns_json, row_count) "
                "VALUES (?, ?, ?, ?)",
                (snapshot_id, table_name, json.dumps(columns, ensure_ascii=False), len(commands)),
            )
            sql = (
                "INSERT INTO _mml_snapshot_rows(snapshot_id, table_name, cmd_type, values_json) " "VALUES (?, ?, ?, ?)"
            )
            batch = []
            for command in commands:
                batch.append(
                    (snapshot_id, table_name, command["cmd_type"], json.dumps(command["values"], ensure_ascii=False))
                )
                if len(batch) >= 2000:
                    db.executemany(sql, batch)
                    batch.clear()
            if batch:
                db.executemany(sql, batch)
        db.execute(
            "INSERT INTO _mml_state(key, value) VALUES ('active_snapshot_id', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (snapshot_id,),
        )


def insert_snapshot_stream(
    snapshot_id: str, name: str, network_element: str, loaded_at: str, commands
) -> Tuple[List[str], int]:
    """Atomically persist an iterator of parsed commands in bounded batches."""
    init_snapshot_schema()
    columns_by_table: Dict[str, set] = {}
    counts: Dict[str, int] = {}
    total = 0
    sql = "INSERT INTO _mml_snapshot_rows(snapshot_id, table_name, cmd_type, values_json) " "VALUES (?, ?, ?, ?)"
    with DatabaseConnection() as db:
        db.execute(
            "INSERT INTO _mml_snapshots(id, name, network_element, loaded_at) VALUES (?, ?, ?, ?)",
            (snapshot_id, name, network_element, loaded_at),
        )
        batch = []
        for command in commands:
            table_name = command["table"]
            if table_name not in columns_by_table:
                columns_by_table[table_name] = set()
                counts[table_name] = 0
                db.execute(
                    "INSERT INTO _mml_snapshot_tables(snapshot_id, table_name, columns_json, row_count) "
                    "VALUES (?, ?, '[]', 0)",
                    (snapshot_id, table_name),
                )
            columns_by_table[table_name].update(command["values"])
            counts[table_name] += 1
            total += 1
            batch.append(
                (
                    snapshot_id,
                    table_name,
                    command["cmd_type"],
                    json.dumps(command["values"], ensure_ascii=False),
                )
            )
            if len(batch) >= 2000:
                db.executemany(sql, batch)
                batch.clear()
        if batch:
            db.executemany(sql, batch)
        if not total:
            raise ValueError("未找到有效的MML命令")
        for table_name, columns in columns_by_table.items():
            db.execute(
                "UPDATE _mml_snapshot_tables SET columns_json=?, row_count=? " "WHERE snapshot_id=? AND table_name=?",
                (json.dumps(sorted(columns), ensure_ascii=False), counts[table_name], snapshot_id, table_name),
            )
        db.execute(
            "INSERT INTO _mml_state(key, value) VALUES ('active_snapshot_id', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (snapshot_id,),
        )
    return list(columns_by_table), total


def list_snapshots_persistent() -> Tuple[List[Dict], Optional[str]]:
    init_snapshot_schema()
    with DatabaseConnection() as db:
        rows = db.execute(
            "SELECT s.*, COALESCE(SUM(t.row_count), 0) AS command_count, COUNT(t.table_name) AS table_count "
            "FROM _mml_snapshots s LEFT JOIN _mml_snapshot_tables t ON t.snapshot_id=s.id "
            "GROUP BY s.id ORDER BY s.loaded_at DESC, s.rowid DESC"
        ).fetchall()
        active = db.execute("SELECT value FROM _mml_state WHERE key='active_snapshot_id'").fetchone()
        return [dict(row) for row in rows], active["value"] if active else None


def activate_snapshot_persistent(snapshot_id: str) -> Optional[Dict]:
    init_snapshot_schema()
    with DatabaseConnection() as db:
        row = db.execute("SELECT * FROM _mml_snapshots WHERE id=?", (snapshot_id,)).fetchone()
        if not row:
            return None
        db.execute(
            "INSERT INTO _mml_state(key, value) VALUES ('active_snapshot_id', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (snapshot_id,),
        )
        return dict(row)


def delete_snapshot_persistent(snapshot_id: str) -> Optional[Dict]:
    """Delete a complete configuration set and select a safe active fallback."""
    init_snapshot_schema()
    with DatabaseConnection() as db:
        row = db.execute("SELECT * FROM _mml_snapshots WHERE id=?", (snapshot_id,)).fetchone()
        if not row:
            return None
        active = db.execute("SELECT value FROM _mml_state WHERE key='active_snapshot_id'").fetchone()
        db.execute("DELETE FROM _mml_snapshots WHERE id=?", (snapshot_id,))

        active_id = active["value"] if active else None
        if active_id == snapshot_id:
            fallback = db.execute(
                "SELECT id FROM _mml_snapshots ORDER BY loaded_at DESC, rowid DESC LIMIT 1"
            ).fetchone()
            active_id = fallback["id"] if fallback else None
            if active_id:
                db.execute(
                    "INSERT INTO _mml_state(key, value) VALUES ('active_snapshot_id', ?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (active_id,),
                )
            else:
                db.execute("DELETE FROM _mml_state WHERE key='active_snapshot_id'")

        result = dict(row)
        result["active_id"] = active_id
        return result


def get_snapshot_tables(snapshot_id: str) -> List[Dict]:
    init_snapshot_schema()
    with DatabaseConnection() as db:
        rows = db.execute(
            "SELECT table_name, columns_json, row_count FROM _mml_snapshot_tables "
            "WHERE snapshot_id=? ORDER BY table_name COLLATE NOCASE",
            (snapshot_id,),
        ).fetchall()
        return [
            {"table_name": row["table_name"], "columns": json.loads(row["columns_json"]), "count": row["row_count"]}
            for row in rows
        ]


def query_snapshot_rows(
    snapshot_id: str,
    table_name: str,
    page: int,
    page_size: int,
    sort_by: str | None,
    sort_order: str,
    filters: Dict[str, str] | None = None,
) -> Tuple[List[Dict], int]:
    """Query a bounded page. JSON fields are sorted in SQLite when requested."""
    offset = (page - 1) * page_size
    order = "DESC" if sort_order.lower() == "desc" else "ASC"
    order_clause = "id ASC"
    where_parts = ["snapshot_id=?", "table_name=?"]
    where_params: list[Any] = [snapshot_id, table_name]
    for field, value in (filters or {}).items():
        where_parts.append(
            "EXISTS (SELECT 1 FROM json_each(values_json) "
            "WHERE json_each.key=? AND CAST(COALESCE(json_each.value, '') AS TEXT) "
            "LIKE ? ESCAPE '\\' COLLATE NOCASE)"
        )
        escaped_value = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        where_params.extend([field, f"%{escaped_value}%"])
    where_clause = " AND ".join(where_parts)

    params = list(where_params)
    if sort_by:
        order_clause = f"json_extract(values_json, ?) {order}, id {order}"
        params.append(f'$."{sort_by.replace(chr(34), chr(34) * 2)}"')
    params.extend([page_size, offset])
    with DatabaseConnection() as db:
        table = db.execute(
            "SELECT 1 FROM _mml_snapshot_tables WHERE snapshot_id=? AND table_name=?",
            (snapshot_id, table_name),
        ).fetchone()
        if not table:
            raise ValueError(f"表 {table_name} 不存在")
        total = db.execute(
            f"SELECT COUNT(*) AS count FROM _mml_snapshot_rows WHERE {where_clause}", where_params
        ).fetchone()["count"]
        rows = db.execute(
            f"SELECT id, cmd_type, values_json FROM _mml_snapshot_rows "
            f"WHERE {where_clause} ORDER BY {order_clause} LIMIT ? OFFSET ?",
            params,
        ).fetchall()
        return [
            {"id": row["id"], "cmd_type": row["cmd_type"], "values": json.loads(row["values_json"])} for row in rows
        ], total


def query_snapshot_row(snapshot_id: str, table_name: str, row_id: int) -> Optional[Dict]:
    with DatabaseConnection() as db:
        row = db.execute(
            "SELECT id, cmd_type, values_json FROM _mml_snapshot_rows " "WHERE snapshot_id=? AND table_name=? AND id=?",
            (snapshot_id, table_name, row_id),
        ).fetchone()
        return {"id": row["id"], "cmd_type": row["cmd_type"], "values": json.loads(row["values_json"])} if row else None


def query_all_snapshot_rows(snapshot_id: str, table_name: str) -> List[Dict]:
    with DatabaseConnection() as db:
        rows = db.execute(
            "SELECT id, cmd_type, values_json FROM _mml_snapshot_rows "
            "WHERE snapshot_id=? AND table_name=? ORDER BY id",
            (snapshot_id, table_name),
        ).fetchall()
        return [
            {"id": row["id"], "cmd_type": row["cmd_type"], "values": json.loads(row["values_json"])} for row in rows
        ]


def insert_snapshot_row(snapshot_id: str, table_name: str, cmd_type: str, values: Dict) -> int:
    with DatabaseConnection() as db:
        table = db.execute(
            "SELECT columns_json FROM _mml_snapshot_tables WHERE snapshot_id=? AND table_name=?",
            (snapshot_id, table_name),
        ).fetchone()
        if not table:
            raise ValueError(f"表 {table_name} 不存在")
        columns = sorted(set(json.loads(table["columns_json"])) | set(values))
        cursor = db.execute(
            "INSERT INTO _mml_snapshot_rows(snapshot_id, table_name, cmd_type, values_json) VALUES (?, ?, ?, ?)",
            (snapshot_id, table_name, cmd_type, json.dumps(values, ensure_ascii=False)),
        )
        db.execute(
            "UPDATE _mml_snapshot_tables SET columns_json=?, row_count=row_count+1 "
            "WHERE snapshot_id=? AND table_name=?",
            (json.dumps(columns, ensure_ascii=False), snapshot_id, table_name),
        )
        return cursor.lastrowid


def update_snapshot_row(snapshot_id: str, table_name: str, row_id: int, values: Dict) -> bool:
    with DatabaseConnection() as db:
        table = db.execute(
            "SELECT columns_json FROM _mml_snapshot_tables WHERE snapshot_id=? AND table_name=?",
            (snapshot_id, table_name),
        ).fetchone()
        if not table:
            raise ValueError(f"表 {table_name} 不存在")
        cursor = db.execute(
            "UPDATE _mml_snapshot_rows SET values_json=? WHERE snapshot_id=? AND table_name=? AND id=?",
            (json.dumps(values, ensure_ascii=False), snapshot_id, table_name, row_id),
        )
        if cursor.rowcount:
            columns = sorted(set(json.loads(table["columns_json"])) | set(values))
            db.execute(
                "UPDATE _mml_snapshot_tables SET columns_json=? WHERE snapshot_id=? AND table_name=?",
                (json.dumps(columns, ensure_ascii=False), snapshot_id, table_name),
            )
        return cursor.rowcount > 0


def delete_snapshot_rows(snapshot_id: str, table_name: str, row_ids: List[int]) -> int:
    if not row_ids:
        return 0
    with DatabaseConnection() as db:
        deleted = 0
        # Stay below SQLite's host-parameter limit for large selections.
        for start in range(0, len(row_ids), 500):
            chunk = row_ids[start : start + 500]
            placeholders = ",".join("?" for _ in chunk)
            cursor = db.execute(
                f"DELETE FROM _mml_snapshot_rows WHERE snapshot_id=? AND table_name=? AND id IN ({placeholders})",
                [snapshot_id, table_name, *chunk],
            )
            deleted += cursor.rowcount
        if deleted:
            db.execute(
                "UPDATE _mml_snapshot_tables SET row_count=row_count-? WHERE snapshot_id=? AND table_name=?",
                (deleted, snapshot_id, table_name),
            )
        return deleted


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
    cursor = db.execute(f"PRAGMA table_info({quote_identifier(table_name)})")
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
                    db.execute(
                        f"ALTER TABLE {quote_identifier(table_name)} " f"ADD COLUMN {quote_identifier(col)} {col_type}"
                    )
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
        cursor = db.execute(f"SELECT COUNT(*) as cnt FROM {quote_identifier(table_name)}")
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
        set_parts.append(f"{quote_identifier(key)} = ?")
        values.append(val)
    if not set_parts:
        return False

    values.append(rowid)
    set_clause = ", ".join(set_parts)
    with DatabaseConnection() as db:
        cursor = db.execute(f"UPDATE {quote_identifier(table_name)} SET {set_clause} WHERE rowid = ?", values)
        return cursor.rowcount > 0


def delete_row(table_name: str, rowid: int) -> bool:
    """删除一行数据，返回是否删除成功"""
    with DatabaseConnection() as db:
        cursor = db.execute(f"DELETE FROM {quote_identifier(table_name)} WHERE rowid = ?", (rowid,))
        return cursor.rowcount > 0


def delete_rows(table_name: str, rowids: List[int]) -> int:
    """批量删除多行数据，返回删除的行数"""
    if not rowids:
        return 0
    placeholders = ",".join(["?"] * len(rowids))
    with DatabaseConnection() as db:
        cursor = db.execute(f"DELETE FROM {quote_identifier(table_name)} WHERE rowid IN ({placeholders})", rowids)
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
    cols_quoted = [quote_identifier(c) for c in columns]
    cols_str = ", ".join(cols_quoted)
    offset = (page - 1) * page_size

    # 排序
    if sort_by and sort_by in columns:
        sort_col = quote_identifier(sort_by)
        order = "ASC" if sort_order.lower() == "asc" else "DESC"
        order_clause = f"ORDER BY {sort_col} {order}"
    else:
        order_clause = "ORDER BY rowid"

    with DatabaseConnection() as db:
        # 总行数
        total = db.execute(f"SELECT COUNT(*) as cnt FROM {quote_identifier(table_name)}").fetchone()["cnt"]

        # 分页数据
        cursor = db.execute(
            f"SELECT rowid, {cols_str} FROM {quote_identifier(table_name)} " f"{order_clause} LIMIT ? OFFSET ?",
            (page_size, offset),
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
    cols_quoted = [quote_identifier(c) for c in columns]
    cols_str = ", ".join(cols_quoted)

    with DatabaseConnection() as db:
        cursor = db.execute(f"SELECT rowid, {cols_str} FROM {quote_identifier(table_name)} WHERE rowid = ?", (rowid,))
        row = cursor.fetchone()
        if not row:
            return None

        row_dict = dict(row)
        config_data = {col: row_dict.get(col) for col in columns}
        return {
            "id": row_dict["rowid"],
            "config_data": config_data,
        }


def query_all_rows(table_name: str, columns: List[str], sort_by: str = None) -> List[Dict]:
    """查询表的所有行（用于导出）"""
    cols_quoted = [quote_identifier(c) for c in columns]
    cols_str = ", ".join(cols_quoted)

    with DatabaseConnection() as db:
        order_clause = f"{quote_identifier(sort_by)}, rowid" if sort_by in columns else "rowid"
        cursor = db.execute(f"SELECT {cols_str} FROM {quote_identifier(table_name)} ORDER BY {order_clause}")
        return [dict(row) for row in cursor.fetchall()]


def query_rows_by_ids(table_name: str, rowids: List[int], columns: List[str]) -> List[Dict]:
    """按 rowid 列表查询多行数据"""
    if not rowids:
        return []
    cols_quoted = [quote_identifier(c) for c in columns]
    cols_str = ", ".join(cols_quoted)
    placeholders = ",".join(["?"] * len(rowids))

    with DatabaseConnection() as db:
        cursor = db.execute(
            f"SELECT rowid, {cols_str} FROM {quote_identifier(table_name)} "
            f"WHERE rowid IN ({placeholders}) ORDER BY rowid",
            rowids,
        )
        return [dict(row) for row in cursor.fetchall()]
