"""Login/logout para o acesso pela porta direta."""

from fastapi import APIRouter, HTTPException, Request, Response

from .. import auth, config
from ..schemas import AuthStatus, LoginIn

router = APIRouter()


@router.get("/auth/status", response_model=AuthStatus)
def status(request: Request):
    via_ingress = auth.is_ingress_request(request)
    user = auth.current_user(request)
    return AuthStatus(
        authenticated=user is not None,
        via_ingress=via_ingress,
        username=user,
        version=config.APP_VERSION,
    )


@router.post("/auth/login", response_model=AuthStatus)
def login(payload: LoginIn, response: Response):
    if not auth.check_credentials(payload.username, payload.password):
        raise HTTPException(401, "Usuário ou senha inválidos")
    auth.issue_session(response, payload.username)
    return AuthStatus(
        authenticated=True,
        via_ingress=False,
        username=payload.username,
        version=config.APP_VERSION,
    )


@router.post("/auth/logout", status_code=204)
def logout(response: Response):
    auth.clear_session(response)
