import csv
import io
import zipfile

from openpyxl import load_workbook

from app.services import mml as mml_service


def test_import_view_edit_and_export_use_memory(tmp_path):
    source = tmp_path / "config.txt"
    source.write_text(
        "ADD USER PROFILE:ID=2,NAME='Jane Doe';\n" "SET USER PROFILE:ID=1,NAME=Admin;\n",
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
    assert 'SET USER PROFILE:ID="1",NAME="Root User";' in exported
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
    assert [table["table_name"] for table in mml_service.get_tables_summary()] == ["alpha", "Middle", "ZEBRA"]


def test_configs_can_be_filtered_by_multiple_columns():
    mml_service.import_mml_text(
        'SET CELL:ID=1,NAME="Alpha_100%"; SET CELL:ID=2,NAME="AlphaX100Y"; SET CELL:ID=3,NAME="Beta";',
        "filters.mml",
    )

    filtered = mml_service.get_configs("CELL", page_size=20, filters={"NAME": "alpha_100%", "ID": "1"})

    assert filtered["total"] == 1
    assert [row["config_data"]["ID"] for row in filtered["configs"]] == [1]


def test_selected_rows_can_be_exported_as_csv_and_excel():
    mml_service.import_mml_text(
        'SET CELL:ID=1,NAME="Alpha"; ADD CELL:ID=2,NAME="Beta";',
        "cells.mml",
    )
    configs = mml_service.get_configs("CELL", page_size=20)["configs"]
    selected_id = next(row["id"] for row in configs if row["config_data"]["ID"] == 2)

    csv_export = mml_service.export_configurations("csv", "CELL", [selected_id])
    csv_rows = list(csv.DictReader(io.StringIO(csv_export["content"].decode("utf-8-sig"))))
    assert csv_export["filename"].startswith("CELL_selected_")
    assert csv_export["media_type"].startswith("text/csv")
    assert csv_export["count"] == 1
    assert csv_rows == [{"ID": "2", "NAME": "Beta"}]

    excel_export = mml_service.export_configurations("xlsx", "CELL", [selected_id])
    workbook = load_workbook(io.BytesIO(excel_export["content"]), read_only=True, data_only=True)
    assert workbook.sheetnames == ["CELL"]
    assert list(workbook["CELL"].values) == [("ID", "NAME"), ("2", "Beta")]
    workbook.close()


def test_all_tables_can_be_exported_as_mml_csv_zip_and_excel():
    mml_service.import_mml_text('SET CELL:ID=1; ADD USER PROFILE:ID=2,NAME="Admin";', "all.mml")

    mml_export = mml_service.export_configurations("mml")
    assert mml_export["count"] == 2
    assert "SET CELL:ID=1;" in mml_export["content"].decode("utf-8-sig")

    csv_export = mml_service.export_configurations("csv")
    assert csv_export["media_type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(csv_export["content"])) as archive:
        assert archive.namelist() == ["CELL.csv", "USER PROFILE.csv"]
        assert "ID" in archive.read("CELL.csv").decode("utf-8-sig")

    excel_export = mml_service.export_configurations("xlsx")
    workbook = load_workbook(io.BytesIO(excel_export["content"]), read_only=True, data_only=True)
    assert workbook.sheetnames == ["CELL", "USER PROFILE"]
    assert list(workbook["CELL"].values) == [("ID",), ("1",)]
    workbook.close()


def test_export_rejects_empty_selection_and_unknown_format():
    mml_service.import_mml_text("SET CELL:ID=1;", "one.mml")

    for export_format, ids in (("pdf", None), ("csv", [])):
        try:
            mml_service.export_configurations(export_format, "CELL", ids)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid export request should fail")
