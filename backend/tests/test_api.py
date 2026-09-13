from unittest.mock import patch

from fastapi.testclient import TestClient

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

        response = client.post("/api/import-mml", files={"file": ("data.csv", b"test")})
        assert response.status_code == 400
        assert response.json() == {"error": "只支持 .mml 或 .txt 格式文件"}


def test_import_accepts_txt_files():
    expected = {"message": "导入成功"}
    with patch("app.api.routes.mml_service.import_mml_stream", return_value=expected):
        with TestClient(app) as client:
            response = client.post(
                "/api/import-mml",
                files={"file": ("commands.TXT", b"SET CELL:ID=1;")},
            )
    assert response.status_code == 200
    assert response.json() == expected


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
