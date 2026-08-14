"""O seed precisa produzir exatamente o gaveteiro físico do usuário."""


def test_seed_cria_12_modulos(client):
    modules = client.get("/api/modules").json()
    assert len(modules) == 12
    assert {m["name"] for m in modules} == {f"M{i}" for i in range(1, 13)}


def test_seed_cria_192_gavetas(client):
    drawers = client.get("/api/drawers").json()
    assert len(drawers) == 192


def test_cada_modulo_tem_16_gavetas(client):
    drawers = client.get("/api/drawers").json()
    por_modulo: dict[str, int] = {}
    for drawer in drawers:
        por_modulo[drawer["module_name"]] = por_modulo.get(drawer["module_name"], 0) + 1
    assert set(por_modulo.values()) == {16}


def test_arranjo_fisico_do_usuario(client):
    posicoes = {m["name"]: (m["grid_col"], m["grid_row"]) for m in client.get("/api/modules").json()}
    assert posicoes["M3"] == (3, 1) and posicoes["M4"] == (4, 1)
    assert posicoes["M9"] == (3, 4) and posicoes["M10"] == (4, 4)
    # A linha de baixo é a única com quatro módulos.
    assert posicoes["M1"] == (1, 5) and posicoes["M2"] == (2, 5)
    assert posicoes["M11"] == (3, 5) and posicoes["M12"] == (4, 5)


def test_gavetas_numeradas_de_1_a_192(client):
    labels = [d["label"] for d in client.get("/api/drawers").json()]
    assert sorted(int(label) for label in labels) == list(range(1, 193))


def test_numeracao_atravessa_modulos_lado_a_lado(client):
    """A linha de cima do M3 e a do M4 são lidas em sequência: 1-4, depois 5-8."""
    por_rotulo = {int(d["label"]): d for d in client.get("/api/drawers").json()}

    # Primeira linha do M3.
    for numero, col in zip(range(1, 5), range(1, 5)):
        assert por_rotulo[numero]["module_name"] == "M3"
        assert (por_rotulo[numero]["row"], por_rotulo[numero]["col"]) == (1, col)

    # Continua na primeira linha do M4, não na segunda do M3.
    for numero, col in zip(range(5, 9), range(1, 5)):
        assert por_rotulo[numero]["module_name"] == "M4"
        assert (por_rotulo[numero]["row"], por_rotulo[numero]["col"]) == (1, col)

    # Só então volta para o M3, agora na segunda linha.
    assert por_rotulo[9]["module_name"] == "M3"
    assert (por_rotulo[9]["row"], por_rotulo[9]["col"]) == (2, 1)


def test_ultima_linha_tem_quatro_modulos(client):
    """M1, M2, M11 e M12 dividem a linha de baixo, então são 16 por linha física."""
    por_rotulo = {int(d["label"]): d for d in client.get("/api/drawers").json()}

    # As quatro linhas de módulos acima consomem 4 x 32 = 128 gavetas.
    assert por_rotulo[129]["module_name"] == "M1"
    assert por_rotulo[133]["module_name"] == "M2"
    assert por_rotulo[137]["module_name"] == "M11"
    assert por_rotulo[141]["module_name"] == "M12"
    assert por_rotulo[145]["module_name"] == "M1"  # volta, segunda linha
    assert por_rotulo[192]["module_name"] == "M12"


def test_seed_e_idempotente(client):
    """Reabrir o app não pode duplicar gavetas."""
    from sqlmodel import Session

    from app.db import get_engine
    from app.seed import seed

    with Session(get_engine()) as session:
        seed(session)
    assert len(client.get("/api/drawers").json()) == 192


def test_mover_modulo_no_grid(client):
    module = client.get("/api/modules").json()[0]
    response = client.patch(f"/api/modules/{module['id']}", json={"grid_col": 2, "grid_row": 7})
    assert response.status_code == 200
    assert response.json()["grid_col"] == 2
    assert response.json()["grid_row"] == 7
