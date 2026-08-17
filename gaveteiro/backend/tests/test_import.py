"""Importação em lote."""


def gaveta(client, label: str) -> dict:
    return next(d for d in client.get("/api/drawers").json() if d["label"] == label)


def test_importa_itens_e_descricao(client):
    payload = {
        "drawers": [
            {
                "label": "1",
                "description": "Resistores 1",
                "items": [
                    {"name": "Resistores 1 10k", "value": "10k", "quantity": 0, "category": "Resistor"},
                    {"name": "Resistores 1 1M", "value": "1M", "quantity": 25, "category": "Resistor"},
                ],
            }
        ]
    }
    response = client.post("/api/import", json=payload)
    assert response.status_code == 200
    assert response.json()["parts_created"] == 2
    assert response.json()["descriptions_set"] == 1

    detalhe = client.get(f"/api/drawers/{gaveta(client, '1')['id']}").json()
    assert detalhe["description"] == "Resistores 1"
    assert sorted(e["quantity"] for e in detalhe["entries"]) == [0, 25]


def test_cria_categoria_que_falta(client):
    antes = {c["name"] for c in client.get("/api/categories").json()}
    client.post(
        "/api/import",
        json={
            "drawers": [
                {"label": "2", "items": [{"name": "Fita isolante", "category": "Consumíveis"}]}
            ]
        },
    )
    depois = {c["name"] for c in client.get("/api/categories").json()}
    assert depois - antes == {"Consumíveis"}


def test_importacao_gera_historico(client):
    client.post(
        "/api/import",
        json={"drawers": [{"label": "3", "items": [{"name": "LED 5mm", "quantity": 40}]}]},
    )
    movimentos = client.get("/api/movements").json()
    assert movimentos[0]["delta"] == 40
    assert movimentos[0]["reason"] == "Importação"


def test_gaveta_inexistente_vai_para_skipped(client):
    response = client.post(
        "/api/import",
        json={"drawers": [{"label": "9999", "items": [{"name": "X"}]}]},
    )
    assert response.json()["skipped"] == ["9999"]
    assert response.json()["parts_created"] == 0


def test_cria_modulo_novo_com_gavetas(client):
    response = client.post(
        "/api/import",
        json={
            "new_modules": [
                {
                    "name": "Extras",
                    "rows": 1,
                    "cols": 2,
                    "grid_col": 9,
                    "grid_row": 9,
                    "drawers": [
                        {"description": "Conectores", "items": [{"name": "KF301-3P", "quantity": 100}]},
                        {"description": "Displays", "items": [{"name": "TFT 2.4", "quantity": 1}]},
                    ],
                }
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["modules_created"] == 1

    novas = [d for d in client.get("/api/drawers").json() if d["module_name"] == "Extras"]
    assert len(novas) == 2
    # Continua a numeração do gaveteiro existente.
    assert sorted(int(d["label"]) for d in novas) == [193, 194]
    assert {d["description"] for d in novas} == {"Conectores", "Displays"}


def test_modulo_repetido_e_ignorado(client):
    corpo = {"new_modules": [{"name": "M1", "drawers": []}]}
    response = client.post("/api/import", json=corpo)
    assert response.json()["modules_created"] == 0
    assert "já existe" in response.json()["skipped"][0]


def test_reset_limpa_antes_de_importar(client):
    """Reimportar depois de renumerar: o conteúdo tem que seguir o número."""
    client.post(
        "/api/import",
        json={"drawers": [{"label": "5", "description": "Antigo", "items": [{"name": "Peça velha"}]}]},
    )
    assert len(client.get("/api/parts").json()) == 1

    client.post(
        "/api/import",
        json={
            "reset": True,
            "drawers": [{"label": "9", "description": "Novo", "items": [{"name": "Peça nova"}]}],
        },
    )

    pecas = client.get("/api/parts").json()
    assert [p["name"] for p in pecas] == ["Peça nova"]
    assert gaveta(client, "5")["description"] == ""
    assert gaveta(client, "5")["part_count"] == 0
    assert gaveta(client, "9")["description"] == "Novo"


def test_reset_limpa_o_historico(client):
    client.post("/api/import", json={"drawers": [{"label": "5", "items": [{"name": "X", "quantity": 3}]}]})
    assert len(client.get("/api/movements").json()) == 1

    client.post("/api/import", json={"reset": True, "drawers": []})
    assert client.get("/api/movements").json() == []
    assert client.get("/api/parts").json() == []


def test_sem_reset_acumula(client):
    corpo = {"drawers": [{"label": "5", "items": [{"name": "Y"}]}]}
    client.post("/api/import", json=corpo)
    client.post("/api/import", json=corpo)
    assert len(client.get("/api/parts").json()) == 2


def test_posicao_ocupada_falha(client):
    ocupado = client.get("/api/modules").json()[0]
    response = client.post(
        "/api/import",
        json={
            "new_modules": [
                {
                    "name": "Novo",
                    "grid_col": ocupado["grid_col"],
                    "grid_row": ocupado["grid_row"],
                    "drawers": [],
                }
            ]
        },
    )
    assert response.status_code == 409
