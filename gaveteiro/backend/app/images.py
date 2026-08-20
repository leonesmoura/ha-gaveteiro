"""Gravação de imagens, compartilhada entre peças e gavetas."""

import uuid

from fastapi import HTTPException, UploadFile
from PIL import Image

from . import config

TIPOS_ACEITOS = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def salvar(file: UploadFile) -> str:
    """Converte para WebP redimensionado e devolve o nome do arquivo."""
    if file.content_type not in TIPOS_ACEITOS:
        raise HTTPException(415, f"Tipo não suportado: {file.content_type}")

    config.ensure_dirs()
    filename = f"{uuid.uuid4().hex}.webp"

    try:
        imagem = Image.open(file.file).convert("RGB")
        imagem.thumbnail((config.IMAGE_MAX_SIZE, config.IMAGE_MAX_SIZE))
        imagem.save(config.IMAGES_DIR / filename, "WEBP", quality=85)
    except OSError as exc:
        raise HTTPException(400, f"Imagem inválida: {exc}") from exc

    return filename


def remover(filename: str | None) -> None:
    if filename:
        (config.IMAGES_DIR / filename).unlink(missing_ok=True)
