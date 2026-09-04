"""Thread-safe in-process store for the active MML configuration snapshot."""

from copy import deepcopy
from datetime import datetime
from threading import RLock


class MemoryConfigStore:
    def __init__(self):
        self._lock = RLock()
        self._tables = {}
        self._loaded_at = None
        self._next_id = 1

    def replace(self, tables):
        with self._lock:
            self._tables = {}
            self._next_id = 1
            self._loaded_at = datetime.now().isoformat()
            for table_name, commands in tables.items():
                columns = sorted({key for command in commands for key in command["values"]})
                rows = []
                for command in commands:
                    rows.append({"id": self._next_id, "cmd_type": command["cmd_type"],
                                 "values": dict(command["values"])})
                    self._next_id += 1
                self._tables[table_name] = {"columns": columns, "rows": rows}

    def snapshot(self):
        with self._lock:
            return deepcopy(self._tables), self._loaded_at

    def add(self, table_name, values, cmd_type="SET"):
        with self._lock:
            table = self._require(table_name)
            table["columns"] = sorted(set(table["columns"]) | set(values))
            row_id = self._next_id
            self._next_id += 1
            table["rows"].append({"id": row_id, "cmd_type": cmd_type, "values": dict(values)})
            return row_id

    def update(self, table_name, row_id, values):
        with self._lock:
            table = self._require(table_name)
            for row in table["rows"]:
                if row["id"] == row_id:
                    row["values"] = dict(values)
                    table["columns"] = sorted(set(table["columns"]) | set(values))
                    return True
            return False

    def delete(self, table_name, row_ids):
        with self._lock:
            table = self._require(table_name)
            wanted = set(row_ids)
            before = len(table["rows"])
            table["rows"] = [row for row in table["rows"] if row["id"] not in wanted]
            return before - len(table["rows"])

    def _require(self, table_name):
        if table_name not in self._tables:
            raise ValueError(f"表 {table_name} 不存在")
        return self._tables[table_name]


store = MemoryConfigStore()
