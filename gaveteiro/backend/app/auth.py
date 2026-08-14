"""Autenticação.

O app é servido por dois caminhos:

  1. Ingress do Home Assistant (sidebar) — o HA já autenticou o usuário e as
     requisições chegam do IP do Supervisor. Liberadas sem login.
  2. Porta direta http://IP:8099 — exige usuário/senha definidos nas opções
     do add-on, com sessão em cookie assinado.

A checagem é pelo IP de origem, não por header, porque header o cliente
forja e IP de origem não.
"""

import hmac
import secrets
from typing import Optional

from fastapi import HTTPException, Request, Response
from itsdangerous import BadSignature, URLSafeTimedSerializer

from . import config

COOKIE_NAME = "gaveteiro_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 dias

_serializer: Optional[URLSafeTimedSerializer] = None


def _get_serializer() -> URLSafeTimedSerializer:
    global _serializer
    if _serializer is None:
        _serializer = URLSafeTimedSerializer(config.session_secret(), salt="gaveteiro-auth")
    return _serializer


def is_ingress_request(request: Request) -> bool:
    client = request.client
    return bool(client and client.host == config.INGRESS_SOURCE_IP)


def check_credentials(username: str, password: str) -> bool:
    """Comparação em tempo constante para não vazar a senha por timing."""
    user_ok = hmac.compare_digest(username, config.AUTH_USER)
    pass_ok = hmac.compare_digest(password, config.AUTH_PASSWORD)
    return user_ok and pass_ok


def issue_session(response: Response, username: str) -> None:
    token = _get_serializer().dumps({"u": username, "n": secrets.token_hex(8)})
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        path="/",
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


def session_username(request: Request) -> Optional[str]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        data = _get_serializer().loads(token, max_age=SESSION_MAX_AGE)
    except BadSignature:
        return None
    except Exception:
        return None
    return data.get("u")


def current_user(request: Request) -> Optional[str]:
    """Quem está falando, ou None se anônimo."""
    if is_ingress_request(request):
        return "home-assistant"
    return session_username(request)


def require_auth(request: Request) -> str:
    """Dependency do FastAPI para proteger rotas."""
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user
