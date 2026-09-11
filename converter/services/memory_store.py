"""Thread-safe in-process store for multiple MML configuration snapshots."""

from copy import deepcopy
from datetime import datetime
from threading import RLock
from uuid import uuid4


class MemoryConfigStore:
    def __init__(self):
        self._lock = RLock()
        self._snapshots = {}
        self._active_id = None
        self._next_row_id = 1

    def add_snapshot(self, tables, name):
        with self._lock:
            snapshot_id = uuid4().hex
            loaded_at = datetime.now().isoformat()
            snapshot_tables = {}
            for table_name, commands in tables.items():
                columns = sorted({key for command in commands for key in command["values"]})
                rows = []
                for command in commands:
                    rows.append({"id": self._next_row_id, "cmd_type": command["cmd_type"],
                                 "values": dict(command["values"])})
                    self._next_row_id += 1
                snapshot_tables[table_name] = {"columns": columns, "rows": rows}
            self._snapshots[snapshot_id] = {
                "id": snapshot_id, "name": name, "loaded_at": loaded_at, "tables": snapshot_tables
            }
            self._active_id = snapshot_id
            return self._metadata(self._snapshots[snapshot_id])

    def list_snapshots(self):
        with self._lock:
            items = [self._metadata(snapshot) for snapshot in self._snapshots.values()]
            return list(reversed(items)), self._active_id

    def activate(self, snapshot_id):
        with self._lock:
            if snapshot_id not in self._snapshots:
                raise ValueError("配置不存在")
            self._active_id = snapshot_id
            return self._metadata(self._snapshots[snapshot_id])

    def snapshot(self, snapshot_id=None):
        with self._lock:
            selected_id = snapshot_id or self._active_id
            if selected_id is None:
                return {}, None
            if selected_id not in self._snapshots:
                raise ValueError("配置不存在")
            selected = self._snapshots[selected_id]
            return deepcopy(selected["tables"]), selected["loaded_at"]

    def add(self, table_name, values, cmd_type="SET"):
        with self._lock:
            table = self._require_table(table_name)
            table["columns"] = sorted(set(table["columns"]) | set(values))
            row_id = self._next_row_id
            self._next_row_id += 1
            table["rows"].append({"id": row_id, "cmd_type": cmd_type, "values": dict(values)})
            return row_id

    def update(self, table_name, row_id, values):
        with self._lock:
            table = self._require_table(table_name)
            for row in table["rows"]:
                if row["id"] == row_id:
                    row["values"] = dict(values)
                    table["columns"] = sorted(set(table["columns"]) | set(values))
                    return True
            return False

    def delete(self, table_name, row_ids):
        with self._lock:
            table = self._require_table(table_name)
            wanted = set(row_ids)
            before = len(table["rows"])
            table["rows"] = [row for row in table["rows"] if row["id"] not in wanted]
            return before - len(table["rows"])

    def _require_table(self, table_name):
        if self._active_id is None:
            raise ValueError("尚未导入配置")
        tables = self._snapshots[self._active_id]["tables"]
        if table_name not in tables:
            raise ValueError(f"表 {table_name} 不存在")
        return tables[table_name]

    @staticmethod
    def _metadata(snapshot):
        return {"id": snapshot["id"], "name": snapshot["name"],
                "loaded_at": snapshot["loaded_at"],
                "table_count": len(snapshot["tables"]),
                "command_count": sum(len(table["rows"]) for table in snapshot["tables"].values())}


store = MemoryConfigStore()
