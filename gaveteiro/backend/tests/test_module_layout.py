"""Arranjo dos módulos (modo de configuração)."""


def modulos(client) -> list[dict]:
    return client.get("/api/modules").json()


def payload(modules: list[dict]) -> dict:
    return {
        "modules": [
            {"id": m["id"], "grid_col": m["grid_col"], "grid_row": m["grid_row"]} for m in modules
        ]
    }


def test_mover_modulo(client):
    atual = modulos(client)
    corpo = payload(atual)
    corpo["modules"][0]["grid_col"] = 1
    corpo["modules"][0]["grid_row"] = 9

    response = client.post("/api/modules/layout", json=corpo)
    assert response.status_code == 200

    movido = next(m for m in modulos(client) if m["id"] == corpo["modules"][0]["id"])
    assert (movido["grid_col"], movido["grid_row"]) == (1, 9)


def test_trocar_dois_modulos_de_lugar(client):
    atual = modulos(client)
    a, b = atual[0], atual[1]
    corpo = payload(atual)
    for item in corpo["modules"]:
        if item["id"] == a["id"]:
            item["grid_col"], item["grid_row"] = b["grid_col"], b["grid_row"]
        elif item["id"] == b["id"]:
            item["grid_col"], item["grid_row"] = a["grid_col"], a["grid_row"]

    assert client.post("/api/modules/layout", json=corpo).status_code == 200

    depois = {m["id"]: (m["grid_col"], m["grid_row"]) for m in modulos(client)}
    assert depois[a["id"]] == (b["grid_col"], b["grid_row"])
    assert depois[b["id"]] == (a["grid_col"], a["grid_row"])


def test_rejeita_dois_na_mesma_celula(client):
    atual = modulos(client)
    corpo = payload(atual)
    corpo["modules"][1]["grid_col"] = corpo["modules"][0]["grid_col"]
    corpo["modules"][1]["grid_row"] = corpo["modules"][0]["grid_row"]

    response = client.post("/api/modules/layout", json=corpo)
    assert response.status_code == 400
    assert "mesma posição" in response.json()["detail"]


def test_rejeita_posicao_zero(client):
    corpo = payload(modulos(client))
    corpo["modules"][0]["grid_col"] = 0
    assert client.post("/api/modules/layout", json=corpo).status_code == 400


def test_renomear_modulo(client):
    atual = modulos(client)
    corpo = payload(atual)
    corpo["modules"][0]["name"] = "Gaveteiro da bancada"

    assert client.post("/api/modules/layout", json=corpo).status_code == 200
    renomeado = next(m for m in modulos(client) if m["id"] == corpo["modules"][0]["id"])
    assert renomeado["name"] == "Gaveteiro da bancada"


def test_rejeita_nome_duplicado(client):
    atual = modulos(client)
    corpo = payload(atual)
    corpo["modules"][0]["name"] = "Igual"
    corpo["modules"][1]["name"] = "Igual"
    assert client.post("/api/modules/layout", json=corpo).status_code == 400


def test_rejeita_nome_vazio(client):
    corpo = payload(modulos(client))
    corpo["modules"][0]["name"] = "   "
    assert client.post("/api/modules/layout", json=corpo).status_code == 400


def test_falha_nao_aplica_nada(client):
    """Posição inválida no fim da lista não pode deixar o resto movido."""
    antes = {m["id"]: (m["grid_col"], m["grid_row"]) for m in modulos(client)}
    corpo = payload(modulos(client))
    corpo["modules"][0]["grid_row"] = 20
    corpo["modules"][-1]["grid_col"] = 0

    assert client.post("/api/modules/layout", json=corpo).status_code == 400
    assert {m["id"]: (m["grid_col"], m["grid_row"]) for m in modulos(client)} == antes


def test_gavetas_seguem_o_modulo(client, part_id):
    """Mover o módulo não mexe no conteúdo das gavetas."""
    drawer = client.get("/api/drawers").json()[0]
    client.post(f"/api/drawers/{drawer['id']}/stock", json={"part_id": part_id, "quantity": 7})

    corpo = payload(modulos(client))
    corpo["modules"][0]["grid_row"] = 8
    client.post("/api/modules/layout", json=corpo)

    assert client.get(f"/api/drawers/{drawer['id']}").json()["entries"][0]["quantity"] == 7
