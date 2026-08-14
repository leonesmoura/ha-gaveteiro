"""Busca, estoque mínimo e autenticação."""

import io

import pytest
from PIL import Image


# --- busca -----------------------------------------------------------------


@pytest.fixture()
def catalogo(client):
    drawers = client.get("/api/drawers").json()
    ids = {}
    for i, (nome, valor, package) in enumerate(
        [("Resistor 10k", "10k", "0805"), ("Capacitor 100n", "100n", "0603"), ("NE555", "", "DIP-8")]
    ):
        part = client.post(
            "/api/parts", json={"name": nome, "value": valor, "package": package}
        ).json()
        client.post(f"/api/drawers/{drawers[i]['id']}/stock", json={"part_id": part["id"], "quantity": 10})
        ids[nome] = (part["id"], drawers[i]["id"])
    return ids


def test_busca_por_valor_devolve_gaveta(client, catalogo):
    result = client.get("/api/search", params={"q": "10k"}).json()
    assert [p["name"] for p in result["parts"]] == ["Resistor 10k"]
    assert result["drawer_ids"] == [catalogo["Resistor 10k"][1]]


def test_busca_por_package(client, catalogo):
    result = client.get("/api/search", params={"q": "DIP"}).json()
    assert [p["name"] for p in result["parts"]] == ["NE555"]


def test_busca_ignora_maiusculas(client, catalogo):
    assert len(client.get("/api/search", params={"q": "resistor"}).json()["parts"]) == 1


def test_busca_sem_resultado(client, catalogo):
    result = client.get("/api/search", params={"q": "zzzz"}).json()
    assert result["parts"] == [] and result["drawer_ids"] == []


def test_busca_vazia_lista_tudo(client, catalogo):
    assert len(client.get("/api/search", params={"q": ""}).json()["parts"]) == 3


# --- estoque mínimo --------------------------------------------------------


def test_estoque_baixo_aparece_na_lista(client, drawer_id):
    part = client.post("/api/parts", json={"name": "LED vermelho", "min_qty": 50}).json()
    client.post(f"/api/drawers/{drawer_id}/stock", json={"part_id": part["id"], "quantity": 10})

    baixo = client.get("/api/parts/low-stock").json()
    assert [p["name"] for p in baixo] == ["LED vermelho"]
    assert baixo[0]["low_stock"] is True


def test_estoque_suficiente_nao_aparece(client, drawer_id):
    part = client.post("/api/parts", json={"name": "LED verde", "min_qty": 50}).json()
    client.post(f"/api/drawers/{drawer_id}/stock", json={"part_id": part["id"], "quantity": 200})
    assert client.get("/api/parts/low-stock").json() == []


def test_gaveta_marca_estoque_baixo(client, drawer_id):
    part = client.post("/api/parts", json={"name": "LED azul", "min_qty": 50}).json()
    client.post(f"/api/drawers/{drawer_id}/stock", json={"part_id": part["id"], "quantity": 3})
    drawer = next(d for d in client.get("/api/drawers").json() if d["id"] == drawer_id)
    assert drawer["low_stock"] is True


# --- imagens ---------------------------------------------------------------


def test_upload_de_imagem(client, part_id):
    buffer = io.BytesIO()
    Image.new("RGB", (2000, 1200), "red").save(buffer, "PNG")
    buffer.seek(0)

    response = client.post(
        f"/api/parts/{part_id}/image",
        files={"file": ("foto.png", buffer, "image/png")},
    )
    assert response.status_code == 200
    image_path = response.json()["image_path"]
    assert image_path.endswith(".webp")
    assert client.get(f"/api/images/{image_path}").status_code == 200


def test_upload_rejeita_tipo_invalido(client, part_id):
    response = client.post(
        f"/api/parts/{part_id}/image",
        files={"file": ("nota.txt", io.BytesIO(b"nao sou imagem"), "text/plain")},
    )
    assert response.status_code == 415


def test_imagem_inexistente(client):
    assert client.get("/api/images/naoexiste.webp").status_code == 404


# --- autenticação ----------------------------------------------------------


def test_sem_sessao_bloqueia(anon_client):
    assert anon_client.get("/api/drawers").status_code == 401


def test_login_com_senha_errada(anon_client):
    response = anon_client.post("/api/auth/login", json={"username": "tester", "password": "errada"})
    assert response.status_code == 401


def test_login_libera_acesso(anon_client):
    assert anon_client.post(
        "/api/auth/login", json={"username": "tester", "password": "segredo"}
    ).status_code == 200
    assert anon_client.get("/api/drawers").status_code == 200


def test_logout_revoga(client):
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/drawers").status_code == 401


def test_ingress_dispensa_login(anon_client, monkeypatch):
    """Requisição vinda do Supervisor do HA já vem autenticada pelo HA."""
    from app import auth

    monkeypatch.setattr(auth, "is_ingress_request", lambda request: True)
    assert anon_client.get("/api/drawers").status_code == 200
    assert anon_client.get("/api/auth/status").json()["via_ingress"] is True


def test_status_reporta_anonimo(anon_client):
    status = anon_client.get("/api/auth/status").json()
    assert status["authenticated"] is False
