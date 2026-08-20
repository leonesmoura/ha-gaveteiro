"""Miniatura por gaveta, com herança da peça."""

import io

import pytest
from PIL import Image


def foto(cor: str = "red") -> io.BytesIO:
    buffer = io.BytesIO()
    Image.new("RGB", (600, 400), cor).save(buffer, "PNG")
    buffer.seek(0)
    return buffer


@pytest.fixture()
def gaveta(client) -> dict:
    return client.get("/api/drawers").json()[0]


def busca(client, drawer_id: int) -> dict:
    return next(d for d in client.get("/api/drawers").json() if d["id"] == drawer_id)


def test_gaveta_sem_foto_nem_peca(client, gaveta):
    assert gaveta["image_path"] is None
    assert gaveta["own_image"] is False


def test_herda_a_foto_da_peca(client, gaveta, part_id):
    client.post(f"/api/drawers/{gaveta['id']}/stock", json={"part_id": part_id, "quantity": 5})
    client.post(f"/api/parts/{part_id}/image", files={"file": ("p.png", foto(), "image/png")})

    fresca = busca(client, gaveta["id"])
    assert fresca["image_path"] is not None
    assert fresca["own_image"] is False


def test_foto_propria_tem_prioridade(client, gaveta, part_id):
    client.post(f"/api/drawers/{gaveta['id']}/stock", json={"part_id": part_id, "quantity": 5})
    client.post(f"/api/parts/{part_id}/image", files={"file": ("p.png", foto("red"), "image/png")})
    herdada = busca(client, gaveta["id"])["image_path"]

    resposta = client.post(
        f"/api/drawers/{gaveta['id']}/image", files={"file": ("g.png", foto("blue"), "image/png")}
    )
    assert resposta.status_code == 200
    assert resposta.json()["own_image"] is True
    assert resposta.json()["image_path"] != herdada


def test_remover_a_propria_volta_a_herdar(client, gaveta, part_id):
    client.post(f"/api/drawers/{gaveta['id']}/stock", json={"part_id": part_id, "quantity": 5})
    client.post(f"/api/parts/{part_id}/image", files={"file": ("p.png", foto(), "image/png")})
    herdada = busca(client, gaveta["id"])["image_path"]

    client.post(f"/api/drawers/{gaveta['id']}/image", files={"file": ("g.png", foto("blue"), "image/png")})
    resposta = client.delete(f"/api/drawers/{gaveta['id']}/image")

    assert resposta.status_code == 200
    assert resposta.json()["own_image"] is False
    assert resposta.json()["image_path"] == herdada


def test_imagem_e_servida(client, gaveta):
    resposta = client.post(
        f"/api/drawers/{gaveta['id']}/image", files={"file": ("g.png", foto(), "image/png")}
    )
    caminho = resposta.json()["image_path"]
    assert caminho.endswith(".webp")
    assert client.get(f"/api/images/{caminho}").status_code == 200


def test_trocar_a_foto_apaga_a_anterior(client, gaveta):
    primeira = client.post(
        f"/api/drawers/{gaveta['id']}/image", files={"file": ("a.png", foto("red"), "image/png")}
    ).json()["image_path"]
    client.post(f"/api/drawers/{gaveta['id']}/image", files={"file": ("b.png", foto("blue"), "image/png")})

    assert client.get(f"/api/images/{primeira}").status_code == 404


def test_tipo_invalido(client, gaveta):
    resposta = client.post(
        f"/api/drawers/{gaveta['id']}/image",
        files={"file": ("x.txt", io.BytesIO(b"nao sou imagem"), "text/plain")},
    )
    assert resposta.status_code == 415


def test_gaveta_inexistente(client):
    assert client.delete("/api/drawers/999999/image").status_code == 404
