"""Aparência aplicada a todos os módulos de uma vez."""


def modulos(client) -> list[dict]:
    return client.get("/api/modules").json()


def test_aplica_proporcao_em_todos(client):
    resposta = client.post("/api/modules/appearance", json={"drawer_ratio": 2.2})
    assert resposta.status_code == 200
    assert {m["drawer_ratio"] for m in modulos(client)} == {2.2}


def test_aplica_escala_em_todos(client):
    client.post("/api/modules/appearance", json={"drawer_scale": 1.6})
    assert {m["drawer_scale"] for m in modulos(client)} == {1.6}


def test_sobrescreve_ajuste_individual(client):
    """O controle geral é o último a falar: zera as diferenças entre módulos."""
    um = modulos(client)[0]
    client.patch(f"/api/modules/{um['id']}", json={"drawer_ratio": 0.7})
    assert len({m["drawer_ratio"] for m in modulos(client)}) == 2

    client.post("/api/modules/appearance", json={"drawer_ratio": 1.5})
    assert {m["drawer_ratio"] for m in modulos(client)} == {1.5}


def test_um_campo_nao_mexe_no_outro(client):
    client.post("/api/modules/appearance", json={"drawer_scale": 2.0})
    client.post("/api/modules/appearance", json={"drawer_ratio": 0.9})
    ms = modulos(client)
    assert {m["drawer_scale"] for m in ms} == {2.0}
    assert {m["drawer_ratio"] for m in ms} == {0.9}


def test_nao_mexe_em_posicao_nem_nome(client):
    antes = {m["id"]: (m["name"], m["grid_col"], m["grid_row"]) for m in modulos(client)}
    client.post("/api/modules/appearance", json={"drawer_ratio": 1.1, "drawer_scale": 1.2})
    assert {m["id"]: (m["name"], m["grid_col"], m["grid_row"]) for m in modulos(client)} == antes


def test_payload_vazio_recusa(client):
    assert client.post("/api/modules/appearance", json={}).status_code == 400


def test_valores_invalidos(client):
    assert client.post("/api/modules/appearance", json={"drawer_ratio": 0}).status_code == 400
    assert client.post("/api/modules/appearance", json={"drawer_scale": -1}).status_code == 400
