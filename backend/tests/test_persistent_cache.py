import io

from app.repositories import sqlite as repository
from app.mml_parser import split_commands_stream
from app.services import mml as mml_service
from app.services.bounded_cache import BoundedLRUCache
from app.services.memory_store import PersistentConfigStore


def _use_test_database(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "_DB_PATH", str(tmp_path / "persistent.db"))


def test_imports_are_persistent_and_isolated_by_configuration_set(tmp_path, monkeypatch):
    _use_test_database(tmp_path, monkeypatch)
    first_store = PersistentConfigStore()
    first = first_store.add_snapshot(
        {"CELL": [{"cmd_type": "SET", "values": {"ID": "1"}}]},
        "same-name.mml",
        "NE-A",
    )
    second = first_store.add_snapshot(
        {"CELL": [{"cmd_type": "SET", "values": {"ID": "2"}}]},
        "same-name.mml",
        "NE-B",
    )

    restarted_store = PersistentConfigStore()
    snapshots, active_id = restarted_store.list_snapshots()
    assert active_id == second["id"]
    assert {item["network_element"] for item in snapshots} >= {"NE-A", "NE-B"}

    restarted_store.activate(first["id"])
    rows, total = restarted_store.query_page("CELL", 1, 20, "ID", "asc")
    assert total == 1
    assert rows[0]["values"]["ID"] == "1"


def test_database_writes_refresh_cached_pages_and_rows(tmp_path, monkeypatch):
    _use_test_database(tmp_path, monkeypatch)
    persistent_store = PersistentConfigStore()
    persistent_store.add_snapshot(
        {"CELL": [{"cmd_type": "SET", "values": {"ID": "1", "NAME": "before"}}]},
        "cell.mml",
        "NE-1",
    )
    rows, _ = persistent_store.query_page("CELL", 1, 20, "ID", "asc")
    row_id = rows[0]["id"]
    assert persistent_store.get("CELL", row_id)["values"]["NAME"] == "before"

    assert persistent_store.update("CELL", row_id, {"ID": "1", "NAME": "after"})
    refreshed, _ = persistent_store.query_page("CELL", 1, 20, "ID", "asc")
    assert refreshed[0]["values"]["NAME"] == "after"
    assert persistent_store.get("CELL", row_id)["values"]["NAME"] == "after"

    persistent_store.add("CELL", {"ID": "2", "NAME": "new"})
    assert persistent_store.table_info("CELL")[0]["count"] == 2
    assert persistent_store.delete("CELL", [row_id]) == 1
    assert persistent_store.get("CELL", row_id) is None
    assert persistent_store.table_info("CELL")[0]["count"] == 1


def test_delete_entire_configuration_cascades_and_selects_fallback(tmp_path, monkeypatch):
    _use_test_database(tmp_path, monkeypatch)
    persistent_store = PersistentConfigStore()
    first = persistent_store.add_snapshot({"FIRST": [{"cmd_type": "SET", "values": {"ID": "1"}}]}, "first.mml", "NE-1")
    second = persistent_store.add_snapshot(
        {"SECOND": [{"cmd_type": "SET", "values": {"ID": "2"}}]}, "second.mml", "NE-2"
    )
    persistent_store.table_summaries()

    deleted = persistent_store.delete_snapshot(second["id"])
    assert deleted["active_id"] == first["id"]
    assert [table["table_name"] for table in persistent_store.table_summaries()[0]] == ["FIRST"]
    with repository.DatabaseConnection() as db:
        assert (
            db.execute(
                "SELECT COUNT(*) AS count FROM _mml_snapshot_rows WHERE snapshot_id=?", (second["id"],)
            ).fetchone()["count"]
            == 0
        )

    deleted = persistent_store.delete_snapshot(first["id"])
    assert deleted["active_id"] is None
    assert persistent_store.list_snapshots() == ([], None)


def test_cache_enforces_entry_total_and_value_limits():
    cache = BoundedLRUCache(max_entries=2, max_bytes=500, max_value_bytes=250)
    assert cache.put(("row", 1), {"value": "a" * 20})
    assert cache.put(("row", 2), {"value": "b" * 20})
    assert cache.put(("row", 3), {"value": "c" * 20})
    assert cache.stats()["entries"] == 2
    assert cache.get(("row", 1)) is None
    assert not cache.put(("large",), {"value": "x" * 1000})
    assert cache.stats()["bytes"] <= cache.stats()["max_bytes"]


def test_streaming_import_handles_chunk_boundaries_and_persists(tmp_path, monkeypatch):
    _use_test_database(tmp_path, monkeypatch)
    monkeypatch.setattr(mml_service, "store", PersistentConfigStore())
    content = (
        "-- exported config\n" "SET CELL:ID=1,NAME='value; still quoted';\n" "ADD CELL:ID=2,NAME=第二行;"
    ).encode("utf-8")
    commands = list(split_commands_stream(io.StringIO(content.decode("utf-8")), chunk_size=7))
    assert len(commands) == 2

    result = mml_service.import_mml_stream(io.BytesIO(content), "ne-stream.mml", "NE-STREAM")
    page = mml_service.get_configs("CELL", page_size=20)

    assert result["total_count"] == 2
    assert result["snapshot"]["network_element"] == "NE-STREAM"
    assert page["total"] == 2
    assert page["configs"][0]["config_data"]["NAME"] == "value; still quoted"
