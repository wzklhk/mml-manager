"""SQLite-backed MML store with a bounded in-process read cache."""

from datetime import datetime
from pathlib import Path
from threading import RLock
from uuid import uuid4

from ..core.config import get_settings
from ..repositories import sqlite as repository
from .bounded_cache import BoundedLRUCache


class PersistentConfigStore:
    def __init__(self):
        settings = get_settings()["cache"]
        self._cache = BoundedLRUCache(settings["max_entries"], settings["max_bytes"], settings["max_value_bytes"])
        self.max_page_size = max(1, int(settings["max_page_size"]))
        self._lock = RLock()
        repository.init_snapshot_schema()

    @staticmethod
    def _metadata(snapshot):
        return {
            "id": snapshot["id"],
            "name": snapshot["name"],
            "network_element": snapshot.get("network_element") or Path(snapshot["name"]).stem,
            "loaded_at": snapshot["loaded_at"],
            "table_count": snapshot.get("table_count", 0),
            "command_count": snapshot.get("command_count", 0),
        }

    def add_snapshot(self, tables, name, network_element=None):
        snapshot_id = uuid4().hex
        loaded_at = datetime.now().isoformat()
        element = (network_element or Path(name).stem or "未命名网元").strip()
        with self._lock:
            repository.insert_snapshot(snapshot_id, name, element, loaded_at, tables)
            self._cache.invalidate()
        return {
            "id": snapshot_id,
            "name": name,
            "network_element": element,
            "loaded_at": loaded_at,
            "table_count": len(tables),
            "command_count": sum(len(commands) for commands in tables.values()),
        }

    def add_snapshot_stream(self, commands, name, network_element=None):
        snapshot_id = uuid4().hex
        loaded_at = datetime.now().isoformat()
        element = (network_element or Path(name).stem or "未命名网元").strip()
        with self._lock:
            table_names, total = repository.insert_snapshot_stream(snapshot_id, name, element, loaded_at, commands)
            self._cache.invalidate()
        return {
            "id": snapshot_id,
            "name": name,
            "network_element": element,
            "loaded_at": loaded_at,
            "table_count": len(table_names),
            "command_count": total,
        }, table_names

    def list_snapshots(self):
        cached = self._cache.get(("snapshots",))
        if cached is not None:
            return cached
        snapshots, active_id = repository.list_snapshots_persistent()
        result = ([self._metadata(snapshot) for snapshot in snapshots], active_id)
        self._cache.put(("snapshots",), result)
        return result

    def active_id(self):
        return self.list_snapshots()[1]

    def activate(self, snapshot_id):
        with self._lock:
            snapshot = repository.activate_snapshot_persistent(snapshot_id)
            if snapshot is None:
                raise ValueError("配置不存在")
            self._cache.invalidate()
        tables = repository.get_snapshot_tables(snapshot_id)
        snapshot["table_count"] = len(tables)
        snapshot["command_count"] = sum(table["count"] for table in tables)
        return self._metadata(snapshot)

    def delete_snapshot(self, snapshot_id):
        with self._lock:
            deleted = repository.delete_snapshot_persistent(snapshot_id)
            if deleted is None:
                raise ValueError("配置不存在")
            self._cache.invalidate()
        metadata = self._metadata(deleted)
        metadata["active_id"] = deleted["active_id"]
        return metadata

    def table_summaries(self, snapshot_id=None):
        selected_id = snapshot_id or self.active_id()
        if selected_id is None:
            return [], None
        key = ("tables", selected_id)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        snapshots, _ = self.list_snapshots()
        selected = next((item for item in snapshots if item["id"] == selected_id), None)
        if selected is None:
            raise ValueError("配置不存在")
        result = (repository.get_snapshot_tables(selected_id), selected["loaded_at"])
        self._cache.put(key, result)
        return result

    def table_info(self, table_name, snapshot_id=None):
        tables, loaded_at = self.table_summaries(snapshot_id)
        table = next((item for item in tables if item["table_name"] == table_name), None)
        if table is None:
            raise ValueError(f"表 {table_name} 不存在")
        return table, loaded_at

    def snapshot(self, snapshot_id=None):
        """Load a complete snapshot for exports only; it is intentionally not cached."""
        selected_id = snapshot_id or self.active_id()
        if selected_id is None:
            return {}, None
        summaries, loaded_at = self.table_summaries(selected_id)
        tables = {
            table["table_name"]: {
                "columns": table["columns"],
                "rows": repository.query_all_snapshot_rows(selected_id, table["table_name"]),
            }
            for table in summaries
        }
        return tables, loaded_at

    def query_page(self, table_name, page, page_size, sort_by=None, sort_order="asc", filters=None):
        selected_id = self.active_id()
        if selected_id is None:
            raise ValueError("尚未导入配置")
        page = max(1, int(page))
        page_size = max(1, min(int(page_size), self.max_page_size))
        normalized_filters = tuple(sorted((filters or {}).items()))
        key = ("page", selected_id, table_name, page, page_size, sort_by, sort_order.lower(), normalized_filters)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        result = repository.query_snapshot_rows(
            selected_id, table_name, page, page_size, sort_by, sort_order, dict(normalized_filters)
        )
        self._cache.put(key, result)
        return result

    def get(self, table_name, row_id):
        selected_id = self.active_id()
        if selected_id is None:
            raise ValueError("尚未导入配置")
        self.table_info(table_name, selected_id)
        key = ("row", selected_id, table_name, int(row_id))
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        row = repository.query_snapshot_row(selected_id, table_name, int(row_id))
        if row is not None:
            self._cache.put(key, row)
        return row

    def _invalidate_table(self, snapshot_id, table_name):
        self._cache.invalidate(
            lambda key: isinstance(key, tuple)
            and (
                key == ("snapshots",)
                or key == ("tables", snapshot_id)
                or (len(key) > 2 and key[1:3] == (snapshot_id, table_name))
            )
        )

    def add(self, table_name, values, cmd_type="SET"):
        selected_id = self.active_id()
        if selected_id is None:
            raise ValueError("尚未导入配置")
        with self._lock:
            row_id = repository.insert_snapshot_row(selected_id, table_name, cmd_type, dict(values))
            self._invalidate_table(selected_id, table_name)
            self._cache.put(
                ("row", selected_id, table_name, row_id),
                {"id": row_id, "cmd_type": cmd_type, "values": dict(values)},
            )
        return row_id

    def update(self, table_name, row_id, values):
        selected_id = self.active_id()
        if selected_id is None:
            raise ValueError("尚未导入配置")
        with self._lock:
            updated = repository.update_snapshot_row(selected_id, table_name, int(row_id), dict(values))
            if updated:
                row = repository.query_snapshot_row(selected_id, table_name, int(row_id))
                self._invalidate_table(selected_id, table_name)
                self._cache.put(("row", selected_id, table_name, int(row_id)), row)
        return updated

    def delete(self, table_name, row_ids):
        selected_id = self.active_id()
        if selected_id is None:
            raise ValueError("尚未导入配置")
        with self._lock:
            deleted = repository.delete_snapshot_rows(selected_id, table_name, [int(item) for item in row_ids])
            if deleted:
                self._invalidate_table(selected_id, table_name)
        return deleted

    def cache_stats(self):
        return self._cache.stats()


# Keep the historic import name stable for extensions importing it directly.
MemoryConfigStore = PersistentConfigStore
store = PersistentConfigStore()
