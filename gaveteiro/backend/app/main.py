"""Aplicação FastAPI: API em ./api e a SPA servida na raiz.

Todas as rotas usam caminhos relativos porque o Ingress do Home Assistant
serve o app sob um prefixo dinâmico (/api/hassio_ingress/<token>/).
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from . import auth, config
from .db import get_engine, init_db
from .routers import auth_routes, importer, layout, parts, search, stock
from .seed import seed

STATIC_DIR = Path(__file__).resolve().parent / "static"

@asynccontextmanager
async def lifespan(_app: FastAPI):
    config.ensure_dirs()
    init_db()
    with Session(get_engine()) as session:
        seed(session)
    yield


app = FastAPI(
    title="Gaveteiro",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# Rotas de autenticação ficam abertas; o resto exige sessão (ou Ingress).
app.include_router(auth_routes.router, prefix="/api")

protected = [Depends(auth.require_auth)]
app.include_router(layout.router, prefix="/api", dependencies=protected)
app.include_router(parts.router, prefix="/api", dependencies=protected)
app.include_router(stock.router, prefix="/api", dependencies=protected)
app.include_router(search.router, prefix="/api", dependencies=protected)
app.include_router(importer.router, prefix="/api", dependencies=protected)


@app.get("/api/images/{filename}")
def get_image(filename: str, _user: str = Depends(auth.require_auth)):
    # Resolve e confere que o arquivo está mesmo dentro de IMAGES_DIR,
    # para um "../" no nome não escapar do diretório.
    target = (config.IMAGES_DIR / filename).resolve()
    if not target.is_file() or config.IMAGES_DIR not in target.parents:
        raise HTTPException(404, "Imagem não encontrada")
    return FileResponse(target, media_type="image/webp")


if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        """Catch-all da SPA. A tela de login é decidida no frontend."""
        if full_path.startswith("api/"):
            raise HTTPException(404, "Rota não encontrada")
        return FileResponse(STATIC_DIR / "index.html")
