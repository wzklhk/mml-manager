import pytest

from app.repositories import sqlite as repository
from app.services.memory_store import store


@pytest.fixture(autouse=True)
def isolated_persistent_store(tmp_path, monkeypatch):
    """Keep all tests away from the application's real SQLite database."""
    monkeypatch.setattr(repository, "_DB_PATH", str(tmp_path / "mml-test.db"))
    store._cache.invalidate()
    yield
    store._cache.invalidate()
