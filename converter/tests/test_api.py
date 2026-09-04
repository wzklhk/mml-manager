import os
import sys
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


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
    with patch("controller.mml_controller.mml_service.import_mml_text", return_value=expected):
        with TestClient(app) as client:
            response = client.post(
                "/api/import-mml",
                files={"file": ("commands.TXT", b"SET CELL:ID=1;")},
            )
    assert response.status_code == 200
    assert response.json() == expected


def test_compare_keeps_existing_response_contract():
    expected = {"summary": {"added": 0, "removed": 0, "modified": 0, "unchanged": 1}, "tables": []}
    with patch("controller.mml_controller.mml_service.compare_mml_texts", return_value=expected):
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
