"""Numeração em pares de módulos.

Cada par (M1/M2, M3/M4, …) consome 32 gavetas e a linha atravessa os dois
módulos do par: M1 leva 1-4 e o M2 continua em 5-8.
"""

import pytest


@pytest.fixture()
def por_rotulo(client) -> dict[int, dict]:
    assert client.post("/api/drawers/renumber", json={"modo": "pares"}).status_code == 200
    return {int(d["label"]): d for d in client.get("/api/drawers").json()}


def test_linha_atravessa_o_par(por_rotulo):
    for numero in range(1, 5):
        assert por_rotulo[numero]["module_name"] == "M1"
    for numero in range(5, 9):
        assert por_rotulo[numero]["module_name"] == "M2"
    # Volta ao M1, agora na segunda linha.
    assert por_rotulo[9]["module_name"] == "M1"
    assert (por_rotulo[9]["row"], por_rotulo[9]["col"]) == (2, 1)


def test_cada_par_consome_32(por_rotulo):
    faixas: dict[str, list[int]] = {}
    for numero, d in por_rotulo.items():
        faixas.setdefault(d["module_name"], []).append(numero)

    assert min(faixas["M1"]) == 1 and max(faixas["M2"]) == 32
    assert min(faixas["M3"]) == 33 and max(faixas["M4"]) == 64
    assert min(faixas["M5"]) == 65 and max(faixas["M6"]) == 96
    assert min(faixas["M11"]) == 161 and max(faixas["M12"]) == 192


def test_exemplo_do_usuario(por_rotulo):
    """Linha de cima do M3 = 33-36, continuando no M4 com 37-40."""
    m3_linha1 = sorted(
        n for n, d in por_rotulo.items() if d["module_name"] == "M3" and d["row"] == 1
    )
    m4_linha1 = sorted(
        n for n, d in por_rotulo.items() if d["module_name"] == "M4" and d["row"] == 1
    )
    assert m3_linha1 == [33, 34, 35, 36]
    assert m4_linha1 == [37, 38, 39, 40]


def test_numeros_do_modulo_ficam_espacados(por_rotulo):
    """M3 leva 33-36, 41-44, 49-52 e 57-60 — não um bloco contínuo."""
    m3 = sorted(n for n, d in por_rotulo.items() if d["module_name"] == "M3")
    assert m3 == [33, 34, 35, 36, 41, 42, 43, 44, 49, 50, 51, 52, 57, 58, 59, 60]


def test_cobre_1_a_192(por_rotulo):
    assert sorted(por_rotulo) == list(range(1, 193))


def test_ordem_independe_da_posicao_fisica(client, por_rotulo):
    """M1 está na linha de baixo do arranjo, mas mesmo assim começa em 1."""
    m1 = next(m for m in client.get("/api/modules").json() if m["name"] == "M1")
    assert m1["grid_row"] == 5  # está embaixo
    assert por_rotulo[1]["module_name"] == "M1"
