"""Configuração lida de variáveis de ambiente.

No add-on, o run.sh exporta essas variáveis a partir das opções do usuário.
Em dev local, os defaults apontam para ./data.
"""

import os
from pathlib import Path


def _path(env: str, default: str) -> Path:
    return Path(os.environ.get(env, default)).resolve()


# Banco fica em /share no add-on para que o SQLite Web consiga abrir o arquivo.
DB_PATH = _path("DB_PATH", "./data/gaveteiro.db")

# Imagens ficam no volume privado do add-on.
DATA_DIR = _path("DATA_DIR", "./data")
IMAGES_DIR = DATA_DIR / "images"

# Credenciais do acesso pela porta direta (http://IP:8099).
AUTH_USER = os.environ.get("AUTH_USER", "admin")
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD", "gaveteiro")

# Chave da sessão. Gerada e persistida em DATA_DIR se não for informada.
SESSION_SECRET = os.environ.get("SESSION_SECRET", "")

# IP do Supervisor do Home Assistant: requisições vindas dele chegam pelo
# Ingress, que já autenticou o usuário no HA.
INGRESS_SOURCE_IP = os.environ.get("INGRESS_SOURCE_IP", "172.30.32.2")

# Versão do add-on, exibida no cabeçalho. O run.sh exporta via bashio.
APP_VERSION = os.environ.get("APP_VERSION", "dev")

# Tamanho máximo do lado maior das imagens salvas.
IMAGE_MAX_SIZE = int(os.environ.get("IMAGE_MAX_SIZE", "800"))


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def session_secret() -> str:
    """Chave estável entre reinícios, para não deslogar todo mundo no restart."""
    if SESSION_SECRET:
        return SESSION_SECRET
    ensure_dirs()
    key_file = DATA_DIR / "session.key"
    if not key_file.exists():
        key_file.write_text(os.urandom(32).hex(), encoding="utf-8")
    return key_file.read_text(encoding="utf-8").strip()
