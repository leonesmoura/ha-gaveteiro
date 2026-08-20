"""Grade e aparência configuráveis por módulo."""


def modulo(client, nome: str) -> dict:
    return next(m for m in client.get("/api/modules").json() if m["name"] == nome)


def gavetas_de(client, nome: str) -> list[dict]:
    return [d for d in client.get("/api/drawers").json() if d["module_name"] == nome]


def test_aumentar_a_grade_cria_gavetas(client):
    m = modulo(client, "M1")
    resposta = client.patch(f"/api/modules/{m['id']}", json={"rows": 5, "cols": 6})
    assert resposta.status_code == 200
    assert (resposta.json()["rows"], resposta.json()["cols"]) == (5, 6)
    assert len(gavetas_de(client, "M1")) == 30


def test_gavetas_existentes_nao_sao_recriadas(client):
    """Aumentar a grade não pode remexer nos rótulos já colados nas gavetas."""
    m = modulo(client, "M1")
    antes = {(d["row"], d["col"]): d["label"] for d in gavetas_de(client, "M1")}

    client.patch(f"/api/modules/{m['id']}", json={"cols": 6})

    depois = {(d["row"], d["col"]): d["label"] for d in gavetas_de(client, "M1")}
    for posicao, rotulo in antes.items():
        assert depois[posicao] == rotulo


def test_novas_gavetas_continuam_a_numeracao(client):
    m = modulo(client, "M1")
    client.patch(f"/api/modules/{m['id']}", json={"cols": 5})
    novas = [d["label"] for d in gavetas_de(client, "M1") if d["col"] == 5]
    assert sorted(int(l) for l in novas) == [193, 194, 195, 196]


def test_reduzir_a_grade_remove_gavetas_vazias(client):
    m = modulo(client, "M1")
    client.patch(f"/api/modules/{m['id']}", json={"rows": 2, "cols": 2})
    assert len(gavetas_de(client, "M1")) == 4


def test_reduzir_recusa_se_a_gaveta_tem_conteudo(client, part_id):
    m = modulo(client, "M1")
    alvo = next(d for d in gavetas_de(client, "M1") if (d["row"], d["col"]) == (4, 4))
    client.post(f"/api/drawers/{alvo['id']}/stock", json={"part_id": part_id, "quantity": 5})

    resposta = client.patch(f"/api/modules/{m['id']}", json={"rows": 2, "cols": 2})
    assert resposta.status_code == 409
    assert alvo["label"] in resposta.json()["detail"]
    # Nada foi removido.
    assert len(gavetas_de(client, "M1")) == 16


def test_grade_invalida(client):
    m = modulo(client, "M1")
    assert client.patch(f"/api/modules/{m['id']}", json={"rows": 0}).status_code == 400


def test_proporcao_e_escala_da_gaveta(client):
    m = modulo(client, "M1")
    resposta = client.patch(
        f"/api/modules/{m['id']}", json={"drawer_ratio": 2.5, "drawer_scale": 1.8}
    )
    assert resposta.status_code == 200
    assert resposta.json()["drawer_ratio"] == 2.5
    assert resposta.json()["drawer_scale"] == 1.8


def test_renomear_pelo_patch(client):
    m = modulo(client, "M1")
    assert client.patch(f"/api/modules/{m['id']}", json={"name": "Bancada"}).status_code == 200
    assert modulo(client, "Bancada")["id"] == m["id"]


def test_renomear_recusa_duplicado(client):
    m = modulo(client, "M1")
    assert client.patch(f"/api/modules/{m['id']}", json={"name": "M2"}).status_code == 409


def test_apagar_modulo_vazio(client):
    m = modulo(client, "M2")
    assert client.delete(f"/api/modules/{m['id']}").status_code == 204
    assert all(x["name"] != "M2" for x in client.get("/api/modules").json())
    assert gavetas_de(client, "M2") == []


def test_apagar_modulo_com_conteudo_recusa(client, part_id):
    m = modulo(client, "M2")
    alvo = gavetas_de(client, "M2")[0]
    client.post(f"/api/drawers/{alvo['id']}/stock", json={"part_id": part_id, "quantity": 1})

    resposta = client.delete(f"/api/modules/{m['id']}")
    assert resposta.status_code == 409
    assert modulo(client, "M2")["id"] == m["id"]


def test_criar_modulo_com_proporcao(client):
    resposta = client.post(
        "/api/modules",
        json={"name": "Fundas", "rows": 2, "cols": 3, "grid_col": 9, "grid_row": 9,
              "drawer_ratio": 0.8, "drawer_scale": 1.5},
    )
    assert resposta.status_code == 201
    assert resposta.json()["drawer_ratio"] == 0.8
    assert len(gavetas_de(client, "Fundas")) == 6
