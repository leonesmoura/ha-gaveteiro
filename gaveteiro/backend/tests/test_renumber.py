"""Renumeração das gavetas."""


def rotulos_por_modulo(client) -> dict[str, list[str]]:
    saida: dict[str, list[str]] = {}
    for d in sorted(client.get("/api/drawers").json(), key=lambda d: (d["row"], d["col"])):
        saida.setdefault(d["module_name"], []).append(d["label"])
    return saida


def test_por_modulo_segue_o_numero_do_modulo(client):
    """M1 fica com 1-16 mesmo estando na linha de baixo do arranjo."""
    response = client.post("/api/drawers/renumber", json={"modo": "por_modulo"})
    assert response.status_code == 200

    por_modulo = rotulos_por_modulo(client)
    assert por_modulo["M1"] == [str(n) for n in range(1, 17)]
    assert por_modulo["M2"] == [str(n) for n in range(17, 33)]
    assert por_modulo["M3"] == [str(n) for n in range(33, 49)]


def test_por_modulo_ordena_m9_antes_de_m10(client):
    """Ordem natural, não alfabética: M9 vem antes de M10, M11, M12."""
    client.post("/api/drawers/renumber", json={"modo": "por_modulo"})
    por_modulo = rotulos_por_modulo(client)
    assert por_modulo["M9"][0] == "129"
    assert por_modulo["M10"][0] == "145"
    assert por_modulo["M12"] == [str(n) for n in range(177, 193)]


def test_continuo_atravessa_modulos(client):
    client.post("/api/drawers/renumber", json={"modo": "continuo"})
    por_rotulo = {d["label"]: d["module_name"] for d in client.get("/api/drawers").json()}
    assert por_rotulo["4"] == "M3"
    assert por_rotulo["5"] == "M4"


def test_inicio_personalizado(client):
    client.post("/api/drawers/renumber", json={"modo": "continuo", "inicio": 101})
    labels = sorted(int(d["label"]) for d in client.get("/api/drawers").json())
    assert labels == list(range(101, 293))


def test_prefixo(client):
    client.post("/api/drawers/renumber", json={"modo": "por_modulo", "prefixo": "G"})
    labels = [d["label"] for d in client.get("/api/drawers").json()]
    assert "G1" in labels and "G192" in labels


def test_ordem_por_coluna(client):
    client.post("/api/drawers/renumber", json={"modo": "por_modulo", "ordem": "coluna"})
    m1 = {d["label"]: (d["row"], d["col"]) for d in client.get("/api/drawers").json() if d["module_name"] == "M1"}
    # Desce a primeira coluna inteira antes de ir para a segunda.
    assert m1["1"] == (1, 1)
    assert m1["2"] == (2, 1)
    assert m1["5"] == (1, 2)


def test_renumerar_preserva_conteudo(client, part_id):
    drawer = client.get("/api/drawers").json()[0]
    client.post(f"/api/drawers/{drawer['id']}/stock", json={"part_id": part_id, "quantity": 42})

    client.post("/api/drawers/renumber", json={"modo": "por_modulo", "inicio": 500})

    detalhe = client.get(f"/api/drawers/{drawer['id']}").json()
    assert detalhe["entries"][0]["quantity"] == 42
    assert detalhe["label"] != drawer["label"]


def test_modo_invalido(client):
    assert client.post("/api/drawers/renumber", json={"modo": "zigzag"}).status_code == 400


def test_renomear_gaveta_individual(client):
    drawer = client.get("/api/drawers").json()[0]
    response = client.patch(f"/api/drawers/{drawer['id']}", json={"label": "Gaveta dos CIs"})
    assert response.status_code == 200
    assert response.json()["label"] == "Gaveta dos CIs"


def test_renomear_rejeita_duplicado(client):
    drawers = client.get("/api/drawers").json()
    response = client.patch(f"/api/drawers/{drawers[0]['id']}", json={"label": drawers[1]["label"]})
    assert response.status_code == 409


def test_renomear_rejeita_vazio(client):
    drawer = client.get("/api/drawers").json()[0]
    assert client.patch(f"/api/drawers/{drawer['id']}", json={"label": "  "}).status_code == 400
