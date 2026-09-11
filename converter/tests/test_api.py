from unittest.mock import patch

from fastapi.testclient import TestClient

from converter.main import app
from converter.services import mml as mml_service


def test_health_and_openapi_are_available():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert client.get("/openapi.json").status_code == 200


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
    with patch("converter.api.routes.mml_service.import_mml_text", return_value=expected):
        with TestClient(app) as client:
            response = client.post(
                "/api/import-mml",
                files={"file": ("commands.TXT", b"SET CELL:ID=1;")},
            )
    assert response.status_code == 200
    assert response.json() == expected


def test_compare_keeps_existing_response_contract():
    expected = {"summary": {"added": 0, "removed": 0, "modified": 0, "unchanged": 1}, "tables": []}
    with patch("converter.api.routes.mml_service.compare_mml_texts", return_value=expected):
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
