"""Gravação de imagens, compartilhada entre peças e gavetas."""

import uuid

from fastapi import HTTPException, UploadFile
from PIL import Image

from . import config

TIPOS_ACEITOS = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _tem_transparencia(imagem: Image.Image) -> bool:
    if imagem.mode in ("RGBA", "LA"):
        return True
    # Paleta com índice transparente (PNG-8 e GIF).
    return imagem.mode == "P" and "transparency" in imagem.info


def salvar(file: UploadFile) -> str:
    """Converte para WebP redimensionado e devolve o nome do arquivo."""
    if file.content_type not in TIPOS_ACEITOS:
        raise HTTPException(415, f"Tipo não suportado: {file.content_type}")

    config.ensure_dirs()
    filename = f"{uuid.uuid4().hex}.webp"

    try:
        imagem = Image.open(file.file)
        # WebP guarda alfa, mas converter para RGB descartaria — e um PNG
        # recortado com fundo transparente ficaria com fundo preto.
        imagem = imagem.convert("RGBA" if _tem_transparencia(imagem) else "RGB")
        imagem.thumbnail((config.IMAGE_MAX_SIZE, config.IMAGE_MAX_SIZE))
        imagem.save(config.IMAGES_DIR / filename, "WEBP", quality=85)
    except OSError as exc:
        raise HTTPException(400, f"Imagem inválida: {exc}") from exc

    return filename


def remover(filename: str | None) -> None:
    if filename:
        (config.IMAGES_DIR / filename).unlink(missing_ok=True)
