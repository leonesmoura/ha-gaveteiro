"""Estoque e histórico. A regra que não pode quebrar: todo ajuste vira Movement."""


def test_atribuir_peca_a_gaveta(client, part_id, drawer_id):
    response = client.post(f"/api/drawers/{drawer_id}/stock", json={"part_id": part_id, "quantity": 100})
    assert response.status_code == 201
    entries = response.json()
    assert len(entries) == 1
    assert entries[0]["quantity"] == 100
    assert entries[0]["part"]["name"] == "Resistor 10k"


def test_ajuste_relativo_gera_movimento(client, part_id, drawer_id):
    client.post(f"/api/drawers/{drawer_id}/stock", json={"part_id": part_id, "quantity": 100})
    client.patch(f"/api/drawers/{drawer_id}/stock/{part_id}", json={"delta": -12, "reason": "Projeto X"})

    entries = client.get(f"/api/drawers/{drawer_id}").json()["entries"]
    assert entries[0]["quantity"] == 88

    movements = client.get("/api/movements", params={"part_id": part_id}).json()
    assert movements[0]["delta"] == -12
    assert movements[0]["resulting_quantity"] == 88
    assert movements[0]["reason"] == "Projeto X"
    assert movements[0]["drawer_label"].isdigit()


def test_ajuste_absoluto(client, part_id, drawer_id):
    client.post(f"/api/drawers/{drawer_id}/stock", json={"part_id": part_id, "quantity": 100})
    response = client.patch(f"/api/drawers/{drawer_id}/stock/{part_id}", json={"set_to": 40})
    assert response.json()[0]["quantity"] == 40

    movements = client.get("/api/movements", params={"part_id": part_id}).json()
    assert movements[0]["delta"] == -60


def test_estoque_nao_fica_negativo(client, part_id, drawer_id):
    client.post(f"/api/drawers/{drawer_id}/stock", json={"part_id": part_id, "quantity": 5})
    response = client.patch(f"/api/drawers/{drawer_id}/stock/{part_id}", json={"delta": -10})
    assert response.status_code == 400
    assert client.get(f"/api/drawers/{drawer_id}").json()["entries"][0]["quantity"] == 5


def test_delta_e_set_to_sao_exclusivos(client, part_id, drawer_id):
    client.post(f"/api/drawers/{drawer_id}/stock", json={"part_id": part_id, "quantity": 5})
    assert client.patch(f"/api/drawers/{drawer_id}/stock/{part_id}", json={}).status_code == 400
    assert (
        client.patch(f"/api/drawers/{drawer_id}/stock/{part_id}", json={"delta": 1, "set_to": 9}).status_code
        == 400
    )


def test_mesma_peca_em_duas_gavetas(client, part_id):
    drawers = client.get("/api/drawers").json()
    a, b = drawers[0]["id"], drawers[1]["id"]
    client.post(f"/api/drawers/{a}/stock", json={"part_id": part_id, "quantity": 30})
    client.post(f"/api/drawers/{b}/stock", json={"part_id": part_id, "quantity": 70})

    part = client.get(f"/api/parts/{part_id}").json()
    assert part["total_quantity"] == 100
    assert len(part["drawer_labels"]) == 2


def test_remover_peca_da_gaveta(client, part_id, drawer_id):
    client.post(f"/api/drawers/{drawer_id}/stock", json={"part_id": part_id, "quantity": 30})
    assert client.delete(f"/api/drawers/{drawer_id}/stock/{part_id}").status_code == 204
    assert client.get(f"/api/drawers/{drawer_id}").json()["entries"] == []
    # A peça continua cadastrada, e o histórico registra a saída.
    assert client.get(f"/api/parts/{part_id}").status_code == 200
    assert client.get("/api/movements", params={"part_id": part_id}).json()[0]["delta"] == -30


def test_resumo_da_gaveta_reflete_totais(client, part_id, drawer_id):
    client.post(f"/api/drawers/{drawer_id}/stock", json={"part_id": part_id, "quantity": 30})
    drawer = next(d for d in client.get("/api/drawers").json() if d["id"] == drawer_id)
    assert drawer["total_quantity"] == 30
    assert drawer["part_count"] == 1
