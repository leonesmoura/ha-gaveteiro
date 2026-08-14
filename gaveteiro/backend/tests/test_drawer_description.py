"""Descrição da gaveta e criação de módulos novos."""


def test_gravar_descricao(client):
    drawer = client.get("/api/drawers").json()[0]
    response = client.patch(f"/api/drawers/{drawer['id']}", json={"description": "Cap. Poliester"})
    assert response.status_code == 200
    assert response.json()["description"] == "Cap. Poliester"


def test_descricao_nao_mexe_no_rotulo(client):
    drawer = client.get("/api/drawers").json()[0]
    client.patch(f"/api/drawers/{drawer['id']}", json={"description": "BJT NPN"})
    assert client.get(f"/api/drawers/{drawer['id']}").json()["label"] == drawer["label"]


def test_rotulo_sozinho_continua_funcionando(client):
    drawer = client.get("/api/drawers").json()[0]
    client.patch(f"/api/drawers/{drawer['id']}", json={"description": "Diodos"})
    client.patch(f"/api/drawers/{drawer['id']}", json={"label": "A1"})
    fresco = client.get(f"/api/drawers/{drawer['id']}").json()
    assert (fresco["label"], fresco["description"]) == ("A1", "Diodos")


def test_criar_modulo_continua_numeracao(client):
    antes = len(client.get("/api/drawers").json())
    response = client.post(
        "/api/modules",
        json={"name": "M13", "rows": 2, "cols": 2, "grid_col": 1, "grid_row": 1},
    )
    assert response.status_code == 201

    drawers = client.get("/api/drawers").json()
    assert len(drawers) == antes + 4
    novos = sorted(int(d["label"]) for d in drawers if d["module_id"] == response.json()["id"])
    assert novos == [193, 194, 195, 196]


def test_criar_modulo_rejeita_posicao_ocupada(client):
    ocupado = client.get("/api/modules").json()[0]
    response = client.post(
        "/api/modules",
        json={"name": "Novo", "grid_col": ocupado["grid_col"], "grid_row": ocupado["grid_row"]},
    )
    assert response.status_code == 409


def test_criar_modulo_rejeita_nome_repetido(client):
    response = client.post("/api/modules", json={"name": "M1", "grid_col": 9, "grid_row": 9})
    assert response.status_code == 409


def test_criar_modulo_com_prefixo(client):
    response = client.post(
        "/api/modules",
        json={"name": "Extras", "rows": 1, "cols": 2, "grid_col": 9, "grid_row": 9, "label_prefix": "E"},
    )
    assert response.status_code == 201
    labels = [d["label"] for d in client.get("/api/drawers").json() if d["module_name"] == "Extras"]
    assert sorted(labels) == ["E193", "E194"]
