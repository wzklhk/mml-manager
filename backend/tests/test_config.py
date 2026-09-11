from pathlib import Path

from app.core.config import load_config


def test_default_database_path_is_outside_source_tree(monkeypatch):
    monkeypatch.delenv("MML_CONFIG_PATH", raising=False)
    database_path = Path(load_config()["database"]["path"])

    assert database_path == Path(__file__).resolve().parents[2] / "data" / "mml_config.db"
    assert "src" not in database_path.parts


def test_external_config_paths_are_relative_to_that_config(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("database:\n  path: runtime/app.db\n", encoding="utf-8")
    monkeypatch.setenv("MML_CONFIG_PATH", str(config_path))

    assert Path(load_config()["database"]["path"]) == tmp_path / "runtime" / "app.db"
