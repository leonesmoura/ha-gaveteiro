"""Importação em lote.

Recebe o gaveteiro já interpretado (gavetas, descrições e itens) e grava tudo
numa transação só. Quem interpreta a planilha é a ferramenta em tools/, para
o add-on não precisar carregar openpyxl.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models import Category, Drawer, Module, Movement, Part, PartTag, Stock
from ..schemas import ImportIn, ImportResult

router = APIRouter()

COR_PADRAO = "#64748b"


def _categoria_id(session: Session, cache: dict[str, int], nome: str) -> int | None:
    if not nome:
        return None
    if nome not in cache:
        existente = session.exec(select(Category).where(Category.name == nome)).first()
        if existente is None:
            existente = Category(name=nome, color=COR_PADRAO)
            session.add(existente)
            session.flush()
        cache[nome] = existente.id
    return cache[nome]


def _preencher(session: Session, cache: dict[str, int], drawer: Drawer, dados) -> int:
    if dados.description:
        drawer.description = dados.description
        session.add(drawer)

    criadas = 0
    for item in dados.items:
        part = Part(
            name=item.name,
            value=item.value,
            package=item.package,
            category_id=_categoria_id(session, cache, item.category),
            notes=item.notes,
        )
        session.add(part)
        session.flush()

        session.add(Stock(drawer_id=drawer.id, part_id=part.id, quantity=item.quantity))
        session.add(
            Movement(
                part_id=part.id,
                drawer_id=drawer.id,
                delta=item.quantity,
                resulting_quantity=item.quantity,
                reason="Importação",
            )
        )
        criadas += 1
    return criadas


def _limpar(session: Session) -> None:
    """Zera o conteúdo, preservando módulos, gavetas e categorias."""
    for stock in session.exec(select(Stock)).all():
        session.delete(stock)
    for movimento in session.exec(select(Movement)).all():
        session.delete(movimento)
    for vinculo in session.exec(select(PartTag)).all():
        session.delete(vinculo)
    session.flush()

    for part in session.exec(select(Part)).all():
        session.delete(part)

    for drawer in session.exec(select(Drawer)).all():
        if drawer.description:
            drawer.description = ""
            session.add(drawer)
    session.flush()


@router.post("/import", response_model=ImportResult)
def importar(payload: ImportIn, session: Session = Depends(get_session)):
    if payload.reset:
        _limpar(session)

    cache: dict[str, int] = {}
    por_rotulo = {d.label: d for d in session.exec(select(Drawer)).all()}

    ignoradas: list[str] = []
    pecas = 0
    descricoes = 0

    for dados in payload.drawers:
        drawer = por_rotulo.get(dados.label)
        if drawer is None:
            ignoradas.append(dados.label)
            continue
        if dados.description:
            descricoes += 1
        pecas += _preencher(session, cache, drawer, dados)

    modulos_criados = 0
    for novo in payload.new_modules:
        if session.exec(select(Module).where(Module.name == novo.name)).first():
            ignoradas.append(f"módulo {novo.name} (já existe)")
            continue

        ocupada = session.exec(
            select(Module).where(Module.grid_col == novo.grid_col, Module.grid_row == novo.grid_row)
        ).first()
        if ocupada:
            raise HTTPException(409, f"Posição do módulo {novo.name} já ocupada por {ocupada.name}")

        module = Module(
            name=novo.name,
            rows=novo.rows,
            cols=novo.cols,
            grid_col=novo.grid_col,
            grid_row=novo.grid_row,
        )
        session.add(module)
        session.flush()
        modulos_criados += 1

        usados = set(por_rotulo)
        numericos = [int(l) for l in usados if l.isdigit()]
        proximo = max(numericos, default=0) + 1

        for indice, dados in enumerate(novo.drawers):
            label = dados.label or str(proximo)
            while label in usados:
                proximo += 1
                label = str(proximo)
            usados.add(label)
            proximo += 1

            drawer = Drawer(
                module_id=module.id,
                row=indice // novo.cols + 1,
                col=indice % novo.cols + 1,
                label=label,
            )
            session.add(drawer)
            session.flush()
            por_rotulo[label] = drawer

            if dados.description:
                descricoes += 1
            pecas += _preencher(session, cache, drawer, dados)

    session.commit()
    return ImportResult(
        parts_created=pecas,
        descriptions_set=descricoes,
        modules_created=modulos_criados,
        skipped=ignoradas,
    )
