"""Thread-safe size-bounded LRU cache used by the MML persistence service."""

from collections import OrderedDict
from copy import deepcopy
from pickle import dumps
from threading import RLock
from typing import Any, Callable, Hashable


class BoundedLRUCache:
    """LRU cache bounded by key count, total bytes and individual value size."""

    def __init__(self, max_entries: int, max_bytes: int, max_value_bytes: int):
        self.max_entries = max(1, int(max_entries))
        self.max_bytes = max(1, int(max_bytes))
        self.max_value_bytes = max(1, int(max_value_bytes))
        self._items: OrderedDict[Hashable, tuple[Any, int]] = OrderedDict()
        self._bytes = 0
        self._lock = RLock()

    def get(self, key: Hashable) -> Any | None:
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            self._items.move_to_end(key)
            return deepcopy(item[0])

    def put(self, key: Hashable, value: Any) -> bool:
        try:
            size = len(dumps((key, value), protocol=5))
        except Exception:
            return False
        if size > self.max_value_bytes or size > self.max_bytes:
            return False
        cached_value = deepcopy(value)
        with self._lock:
            old = self._items.pop(key, None)
            if old:
                self._bytes -= old[1]
            self._items[key] = (cached_value, size)
            self._bytes += size
            while len(self._items) > self.max_entries or self._bytes > self.max_bytes:
                _, (_, removed_size) = self._items.popitem(last=False)
                self._bytes -= removed_size
        return True

    def invalidate(self, predicate: Callable[[Hashable], bool] | None = None) -> None:
        with self._lock:
            if predicate is None:
                self._items.clear()
                self._bytes = 0
                return
            for key in [key for key in self._items if predicate(key)]:
                _, size = self._items.pop(key)
                self._bytes -= size

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "entries": len(self._items),
                "bytes": self._bytes,
                "max_entries": self.max_entries,
                "max_bytes": self.max_bytes,
                "max_value_bytes": self.max_value_bytes,
            }
