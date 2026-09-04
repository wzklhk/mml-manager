from service import mml_service


def test_import_view_edit_and_export_use_memory(tmp_path):
    source = tmp_path / "config.txt"
    source.write_text(
        "ADD USER PROFILE:ID=2,NAME='Jane Doe';\n"
        "SET USER PROFILE:ID=1,NAME=Admin;\n",
        encoding="utf-8",
    )

    imported = mml_service.import_mml_file(str(source))
    summary = mml_service.get_tables_summary()
    page = mml_service.get_configs("USER PROFILE", page=1, page_size=20)

    assert imported["total_count"] == 2
    assert summary[0]["count"] == 2
    assert [row["cmd_type"] for row in page["configs"]] == ["SET", "ADD"]

    row_id = page["configs"][0]["id"]
    assert mml_service.update_config("USER PROFILE", row_id, {"ID": "1", "NAME": "Root User"})
    exported = mml_service.export_mml("USER PROFILE")["content"]
    assert 'SET USER PROFILE:ID=1,NAME="Root User";' in exported
    assert "ADD USER PROFILE:ID=2,NAME=Jane Doe;" not in exported
    assert 'ADD USER PROFILE:ID=2,NAME="Jane Doe";' in exported


def test_each_import_is_retained_and_can_be_activated(tmp_path):
    first = tmp_path / "first.mml"
    second = tmp_path / "second.mml"
    first.write_text("SET FIRST:ID=1;", encoding="utf-8")
    second.write_text("SET SECOND:ID=2;", encoding="utf-8")

    first_result = mml_service.import_mml_file(str(first))
    second_result = mml_service.import_mml_file(str(second))

    assert [table["table_name"] for table in mml_service.get_tables_summary()] == ["SECOND"]
    snapshots = mml_service.get_snapshots()
    assert len(snapshots["snapshots"]) >= 2
    assert snapshots["active_id"] == second_result["snapshot"]["id"]

    mml_service.activate_snapshot(first_result["snapshot"]["id"])
    assert [table["table_name"] for table in mml_service.get_tables_summary()] == ["FIRST"]


def test_table_summary_is_sorted_by_command_name():
    mml_service.import_mml_text("SET ZEBRA:ID=1; SET alpha:ID=2; SET Middle:ID=3;", "sorted.mml")
    assert [table["table_name"] for table in mml_service.get_tables_summary()] == [
        "alpha", "Middle", "ZEBRA"
    ]
