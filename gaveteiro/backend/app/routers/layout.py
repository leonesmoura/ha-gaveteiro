"""Módulos e gavetas — o que o grid interativo desenha."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models import Drawer, Module
from ..queries import drawer_entries, drawer_summaries
from ..schemas import (
    DrawerDetail,
    DrawerOut,
    DrawerRename,
    ModuleCreate,
    ModuleLayoutIn,
    ModuleOut,
    ModuleUpdate,
    RenumberIn,
)
from ..seed import numerar

router = APIRouter()


@router.get("/modules", response_model=list[ModuleOut])
def list_modules(session: Session = Depends(get_session)):
    return session.exec(select(Module).order_by(Module.grid_row, Module.grid_col)).all()


@router.patch("/modules/{module_id}", response_model=ModuleOut)
def update_module(module_id: int, payload: ModuleUpdate, session: Session = Depends(get_session)):
    module = session.get(Module, module_id)
    if module is None:
        raise HTTPException(404, "Módulo não encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(module, field, value)
    session.add(module)
    session.commit()
    session.refresh(module)
    return module


@router.post("/modules", response_model=ModuleOut, status_code=201)
def create_module(payload: ModuleCreate, session: Session = Depends(get_session)):
    """Cria um módulo e as gavetas dele, continuando a numeração existente."""
    if payload.rows < 1 or payload.cols < 1:
        raise HTTPException(400, "O módulo precisa de ao menos uma linha e uma coluna")

    nome = payload.name.strip()
    if not nome:
        raise HTTPException(400, "O nome do módulo não pode ficar vazio")
    if session.exec(select(Module).where(Module.name == nome)).first():
        raise HTTPException(409, f"Já existe um módulo chamado {nome}")

    ocupado = session.exec(
        select(Module).where(
            Module.grid_col == payload.grid_col, Module.grid_row == payload.grid_row
        )
    ).first()
    if ocupado:
        raise HTTPException(409, f"A posição já é ocupada por {ocupado.name}")

    module = Module(
        name=nome,
        rows=payload.rows,
        cols=payload.cols,
        grid_col=payload.grid_col,
        grid_row=payload.grid_row,
    )
    session.add(module)
    session.flush()

    # Continua a numeração: pega o maior rótulo puramente numérico existente.
    existentes = session.exec(select(Drawer.label)).all()
    numericos = [int(l) for l in existentes if l.isdigit()]
    proximo = max(numericos, default=0) + 1

    usados = set(existentes)
    for row in range(1, payload.rows + 1):
        for col in range(1, payload.cols + 1):
            label = f"{payload.label_prefix}{proximo}"
            while label in usados:
                proximo += 1
                label = f"{payload.label_prefix}{proximo}"
            usados.add(label)
            session.add(Drawer(module_id=module.id, row=row, col=col, label=label))
            proximo += 1

    session.commit()
    session.refresh(module)
    return module


@router.post("/modules/layout", response_model=list[ModuleOut])
def set_layout(payload: ModuleLayoutIn, session: Session = Depends(get_session)):
    """Aplica o arranjo inteiro de uma vez.

    Em bloco porque mover módulos é uma operação só do ponto de vista do
    usuário: aplicar pela metade deixaria dois módulos na mesma célula.
    """
    if not payload.modules:
        raise HTTPException(400, "Nenhum módulo informado")

    celulas = [(m.grid_col, m.grid_row) for m in payload.modules]
    if len(set(celulas)) != len(celulas):
        raise HTTPException(400, "Dois módulos não podem ocupar a mesma posição")

    if any(m.grid_col < 1 or m.grid_row < 1 for m in payload.modules):
        raise HTTPException(400, "Linha e coluna começam em 1")

    nomes = [m.name.strip() for m in payload.modules if m.name is not None]
    if len(set(nomes)) != len(nomes):
        raise HTTPException(400, "Dois módulos não podem ter o mesmo nome")
    if any(not nome for nome in nomes):
        raise HTTPException(400, "O nome do módulo não pode ficar vazio")

    for item in payload.modules:
        module = session.get(Module, item.id)
        if module is None:
            raise HTTPException(404, f"Módulo {item.id} não encontrado")
        module.grid_col = item.grid_col
        module.grid_row = item.grid_row
        if item.name is not None:
            module.name = item.name.strip()
        session.add(module)

    session.commit()
    return session.exec(select(Module).order_by(Module.grid_row, Module.grid_col)).all()


@router.get("/drawers", response_model=list[DrawerOut])
def list_drawers(session: Session = Depends(get_session)):
    return drawer_summaries(session)


@router.post("/drawers/renumber", response_model=list[DrawerOut])
def renumber(payload: RenumberIn, session: Session = Depends(get_session)):
    """Refaz os rótulos de todas as gavetas segundo o esquema escolhido.

    Só muda rótulo: o conteúdo das gavetas continua onde está.
    """
    modules = session.exec(select(Module)).all()
    try:
        plano = numerar(
            list(modules),
            modo=payload.modo,
            inicio=payload.inicio,
            ordem=payload.ordem,
            prefixo=payload.prefixo,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    drawers = session.exec(select(Drawer)).all()
    por_posicao = {(d.module_id, d.row, d.col): d for d in drawers}

    novos = {(m.id, row, col): label for m, row, col, label in plano}
    if len(set(novos.values())) != len(novos):
        raise HTTPException(400, "O esquema escolhido geraria rótulos repetidos")

    faltando = set(por_posicao) - set(novos)
    if faltando:
        raise HTTPException(400, "Há gavetas fora do arranjo atual dos módulos")

    # Rótulos são únicos: passa por um nome temporário para não colidir com
    # um rótulo que ainda pertence a outra gaveta no meio da troca.
    for drawer in drawers:
        drawer.label = f"~{drawer.id}"
        session.add(drawer)
    session.flush()

    for posicao, label in novos.items():
        drawer = por_posicao.get(posicao)
        if drawer is not None:
            drawer.label = label
            session.add(drawer)

    session.commit()
    return drawer_summaries(session)


@router.patch("/drawers/{drawer_id}", response_model=DrawerOut)
def rename_drawer(drawer_id: int, payload: DrawerRename, session: Session = Depends(get_session)):
    drawer = session.get(Drawer, drawer_id)
    if drawer is None:
        raise HTTPException(404, "Gaveta não encontrada")

    if payload.label is not None:
        label = payload.label.strip()
        if not label:
            raise HTTPException(400, "O rótulo não pode ficar vazio")

        conflito = session.exec(select(Drawer).where(Drawer.label == label)).first()
        if conflito is not None and conflito.id != drawer_id:
            raise HTTPException(409, f"Já existe uma gaveta com o rótulo {label}")
        drawer.label = label

    if payload.description is not None:
        drawer.description = payload.description.strip()

    session.add(drawer)
    session.commit()

    return next(d for d in drawer_summaries(session) if d.id == drawer_id)


@router.get("/drawers/{drawer_id}", response_model=DrawerDetail)
def get_drawer(drawer_id: int, session: Session = Depends(get_session)):
    drawer = session.get(Drawer, drawer_id)
    if drawer is None:
        raise HTTPException(404, "Gaveta não encontrada")
    summary = next(d for d in drawer_summaries(session) if d.id == drawer_id)
    return DrawerDetail(**summary.model_dump(), entries=drawer_entries(session, drawer))
