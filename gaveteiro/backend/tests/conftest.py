import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """App isolado: banco e imagens num tmp_path, credenciais conhecidas.

    Os módulos não são reimportados (o metadata do SQLModel é global e
    reclamaria de tabelas duplicadas); em vez disso reconfiguramos os
    atributos e zeramos a engine.
    """
    from fastapi.testclient import TestClient

    from app import auth, config, db
    from app.main import app

    data_dir = tmp_path / "data"
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(config, "DATA_DIR", data_dir)
    monkeypatch.setattr(config, "IMAGES_DIR", data_dir / "images")
    monkeypatch.setattr(config, "AUTH_USER", "tester")
    monkeypatch.setattr(config, "AUTH_PASSWORD", "segredo")
    monkeypatch.setattr(config, "SESSION_SECRET", "chave-de-teste")
    monkeypatch.setattr(db, "_engine", None)
    monkeypatch.setattr(auth, "_serializer", None)

    with TestClient(app) as test_client:
        test_client.post("/api/auth/login", json={"username": "tester", "password": "segredo"})
        yield test_client

    db._engine = None


@pytest.fixture()
def anon_client(client):
    """Mesmo app, sem cookie de sessão."""
    client.cookies.clear()
    return client


@pytest.fixture()
def part_id(client):
    response = client.post(
        "/api/parts",
        json={"name": "Resistor 10k", "value": "10k", "package": "0805", "min_qty": 50},
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture()
def drawer_id(client):
    return client.get("/api/drawers").json()[0]["id"]
