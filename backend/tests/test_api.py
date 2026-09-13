import io
from unittest.mock import patch

from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.main import app
from app.services import mml as mml_service


def test_health_and_openapi_are_available():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert client.get("/openapi.json").status_code == 200


def test_static_assets_are_not_intercepted_by_spa_fallback(tmp_path, monkeypatch):
    javascript = tmp_path / "app.js"
    javascript.write_text("console.log('ok')", encoding="utf-8")
    monkeypatch.setattr("app.main.STATIC_DIR", tmp_path)

    from app.main import create_app

    with TestClient(create_app()) as client:
        response = client.get("/static/app.js")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/javascript")
    assert response.text == "console.log('ok')"


def test_import_rejects_missing_or_wrong_file_type():
    with TestClient(app) as client:
        response = client.post("/api/import-mml")
        assert response.status_code == 400
        assert response.json() == {"error": "未上传文件"}

        response = client.post("/api/import-mml", files={"file": ("data.pdf", b"test")})
        assert response.status_code == 400
        assert response.json() == {"error": "只支持 .mml、.txt、.csv 或 .xlsx 格式文件"}


def test_import_accepts_txt_files():
    expected = {"message": "导入成功"}
    with patch("app.api.routes.mml_service.import_configuration_stream", return_value=expected):
        with TestClient(app) as client:
            response = client.post(
                "/api/import-mml",
                files={"file": ("commands.TXT", b"SET CELL:ID=1;")},
            )
    assert response.status_code == 200
    assert response.json() == expected


def test_import_csv_infers_scalar_types_and_preserves_leading_zero_strings():
    content = b"NUMBER,DECIMAL,CODE,ENABLED,NAME\n42,-2.5,001,true,Alpha\n"

    with TestClient(app) as client:
        response = client.post("/api/import-mml", files={"file": ("cells.csv", content)})
        configs = client.get("/api/configs", params={"table_name": "cells"})

    assert response.status_code == 200
    assert response.json()["total_count"] == 1
    assert configs.status_code == 200
    assert configs.json()["configs"][0]["config_data"] == {
        "CODE": "001",
        "DECIMAL": -2.5,
        "ENABLED": True,
        "NAME": "Alpha",
        "NUMBER": 42,
    }


def test_import_excel_preserves_native_cell_types_and_multiple_sheets():
    workbook = Workbook()
    cells = workbook.active
    cells.title = "CELL"
    cells.append(["NUMBER", "CODE", "NAME"])
    cells.append([42, "042", "Alpha"])
    users = workbook.create_sheet("USER PROFILE")
    users.append(["ID", "NAME"])
    users.append([7, "Admin"])
    content = io.BytesIO()
    workbook.save(content)
    workbook.close()

    with TestClient(app) as client:
        response = client.post(
            "/api/import-mml",
            files={"file": ("configs.xlsx", content.getvalue())},
        )
        cells_response = client.get("/api/configs", params={"table_name": "CELL"})
        users_response = client.get("/api/configs", params={"table_name": "USER PROFILE"})

    assert response.status_code == 200
    assert response.json()["total_count"] == 2
    assert response.json()["tables"] == ["CELL", "USER PROFILE"]
    assert cells_response.json()["configs"][0]["config_data"] == {
        "CODE": "042",
        "NAME": "Alpha",
        "NUMBER": 42,
    }
    assert users_response.json()["configs"][0]["config_data"] == {"ID": 7, "NAME": "Admin"}


def test_compare_keeps_existing_response_contract():
    expected = {"summary": {"added": 0, "removed": 0, "modified": 0, "unchanged": 1}, "tables": []}
    with patch("app.api.routes.mml_service.compare_mml_texts", return_value=expected):
        with TestClient(app) as client:
            response = client.post(
                "/api/compare-mml",
                files={
                    "baseline": ("base.txt", b"SET CELL:ID=1;"),
                    "target": ("target.mml", b"SET CELL:ID=1;"),
                },
            )
    assert response.status_code == 200
    assert response.json() == expected


def test_compare_persisted_configurations_endpoint():
    baseline = mml_service.import_mml_text("SET CELL:ID=1,POWER=40;", "baseline.mml")
    target = mml_service.import_mml_text("SET CELL:ID=1,POWER=42;", "target.mml")

    with TestClient(app) as client:
        response = client.post(
            "/api/compare-configurations",
            json={"baseline_id": baseline["snapshot"]["id"], "target_id": target["snapshot"]["id"]},
        )

    assert response.status_code == 200
    assert response.json()["summary"] == {"added": 0, "removed": 0, "modified": 1, "unchanged": 0}


def test_snapshot_list_and_activation_endpoints():
    first = mml_service.import_mml_text("SET FIRST:ID=1;", "first.mml")
    second = mml_service.import_mml_text("SET SECOND:ID=2;", "second.mml")
    with TestClient(app) as client:
        listed = client.get("/api/snapshots")
        assert listed.status_code == 200
        assert listed.json()["active_id"] == second["snapshot"]["id"]

        activated = client.post(f"/api/snapshots/{first['snapshot']['id']}/activate")
        assert activated.status_code == 200
        assert activated.json()["snapshot"]["name"] == "first.mml"


def test_create_empty_configuration_endpoint():
    with TestClient(app) as client:
        response = client.post("/api/snapshots", json={"name": "Manual Config"})
        listed = client.get("/api/snapshots")
        tables = client.get("/api/tables")

    assert response.status_code == 201
    assert response.json()["snapshot"]["name"] == "Manual Config"
    assert response.json()["total_count"] == 0
    assert listed.json()["active_id"] == response.json()["snapshot"]["id"]
    assert tables.json()["tables"] == []


def test_create_and_delete_table_endpoints():
    mml_service.import_mml_text("SET EXISTING:ID=1;", "tables.mml")

    with TestClient(app) as client:
        created = client.post("/api/tables", json={"table_name": "NEW TABLE", "columns": ["ID", "NAME"]})
        listed = client.get("/api/tables")
        deleted = client.post("/api/tables/delete", json={"table_name": "NEW TABLE"})

    assert created.status_code == 201
    assert created.json()["table"] == {"table_name": "NEW TABLE", "columns": ["ID", "NAME"], "count": 0}
    assert "NEW TABLE" in {table["table_name"] for table in listed.json()["tables"]}
    assert deleted.status_code == 200
    assert deleted.json()["table_name"] == "NEW TABLE"


def test_delete_snapshot_endpoint_removes_complete_configuration():
    imported = mml_service.import_mml_text("SET DELETE_ME:ID=1;", "delete-me.mml")
    with TestClient(app) as client:
        response = client.delete(f"/api/snapshots/{imported['snapshot']['id']}")

    assert response.status_code == 200
    assert response.json()["deleted"]["name"] == "delete-me.mml"
    assert imported["snapshot"]["id"] not in {item["id"] for item in mml_service.get_snapshots()["snapshots"]}


def test_post_delete_snapshot_endpoint_for_restricted_http_environments():
    imported = mml_service.import_mml_text("SET DELETE_POST:ID=1;", "delete-post.mml")
    with TestClient(app) as client:
        response = client.post(f"/api/snapshots/{imported['snapshot']['id']}/delete")

    assert response.status_code == 200
    assert response.json()["deleted"]["name"] == "delete-post.mml"


def test_export_endpoint_downloads_selected_csv():
    mml_service.import_mml_text("SET CELL:ID=1,NAME=Alpha; SET CELL:ID=2,NAME=Beta;", "cells.mml")
    selected = mml_service.get_configs("CELL", page_size=20)["configs"][0]

    with TestClient(app) as client:
        response = client.post(
            "/api/export",
            json={"format": "csv", "table_name": "CELL", "ids": [selected["id"]]},
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "filename*=UTF-8''CELL_selected_" in response.headers["content-disposition"]
    assert response.headers["x-export-count"] == "1"
    assert "Alpha" in response.content.decode("utf-8-sig")


def test_export_endpoint_rejects_unknown_format():
    with TestClient(app) as client:
        response = client.post("/api/export", json={"format": "pdf"})

    assert response.status_code == 400
    assert "只支持" in response.json()["error"]


def test_configs_reject_malformed_filters():
    with TestClient(app) as client:
        response = client.get("/api/configs", params={"table_name": "CELL", "filters": "not-json"})

    assert response.status_code == 400
    assert response.json() == {"error": "筛选条件格式无效"}
