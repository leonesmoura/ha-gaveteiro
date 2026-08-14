"""Estoque e histórico de movimentos.

Regra central: nenhuma quantidade muda sem gerar um Movement.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..db import get_session
from ..models import Drawer, Movement, Part, Stock
from ..queries import drawer_entries
from ..schemas import MovementOut, StockAdjust, StockAssign, StockEntryOut

router = APIRouter()


def _record(session: Session, part_id: int, drawer_id: int, delta: int, resulting: int, reason: str) -> None:
    session.add(
        Movement(
            part_id=part_id,
            drawer_id=drawer_id,
            delta=delta,
            resulting_quantity=resulting,
            reason=reason,
        )
    )


@router.post("/drawers/{drawer_id}/stock", response_model=list[StockEntryOut], status_code=201)
def assign_part(drawer_id: int, payload: StockAssign, session: Session = Depends(get_session)):
    """Coloca uma peça na gaveta. Se já estiver lá, soma à quantidade."""
    drawer = session.get(Drawer, drawer_id)
    if drawer is None:
        raise HTTPException(404, "Gaveta não encontrada")
    if session.get(Part, payload.part_id) is None:
        raise HTTPException(404, "Peça não encontrada")
    if payload.quantity < 0:
        raise HTTPException(400, "Quantidade não pode ser negativa")

    stock = session.get(Stock, (drawer_id, payload.part_id))
    if stock is None:
        stock = Stock(drawer_id=drawer_id, part_id=payload.part_id, quantity=payload.quantity)
        delta = payload.quantity
    else:
        delta = payload.quantity
        stock.quantity += payload.quantity

    session.add(stock)
    _record(session, payload.part_id, drawer_id, delta, stock.quantity, "Peça atribuída à gaveta")
    session.commit()
    session.refresh(drawer)
    return drawer_entries(session, drawer)


@router.patch("/drawers/{drawer_id}/stock/{part_id}", response_model=list[StockEntryOut])
def adjust_stock(
    drawer_id: int,
    part_id: int,
    payload: StockAdjust,
    session: Session = Depends(get_session),
):
    stock = session.get(Stock, (drawer_id, part_id))
    if stock is None:
        raise HTTPException(404, "Essa peça não está nessa gaveta")
    if (payload.delta is None) == (payload.set_to is None):
        raise HTTPException(400, "Informe delta OU set_to")

    previous = stock.quantity
    new_quantity = previous + payload.delta if payload.delta is not None else payload.set_to
    if new_quantity < 0:
        raise HTTPException(400, "Estoque não pode ficar negativo")

    stock.quantity = new_quantity
    session.add(stock)
    _record(session, part_id, drawer_id, new_quantity - previous, new_quantity, payload.reason)
    session.commit()

    drawer = session.get(Drawer, drawer_id)
    return drawer_entries(session, drawer)


@router.delete("/drawers/{drawer_id}/stock/{part_id}", status_code=204)
def remove_from_drawer(drawer_id: int, part_id: int, session: Session = Depends(get_session)):
    """Tira a peça da gaveta (a peça em si continua cadastrada)."""
    stock = session.get(Stock, (drawer_id, part_id))
    if stock is None:
        raise HTTPException(404, "Essa peça não está nessa gaveta")
    _record(session, part_id, drawer_id, -stock.quantity, 0, "Peça retirada da gaveta")
    session.delete(stock)
    session.commit()


@router.get("/movements", response_model=list[MovementOut])
def list_movements(
    part_id: int | None = None,
    drawer_id: int | None = None,
    limit: int = Query(default=100, le=500),
    session: Session = Depends(get_session),
):
    query = select(Movement, Part, Drawer).join(Part, Part.id == Movement.part_id).join(
        Drawer, Drawer.id == Movement.drawer_id
    )
    if part_id is not None:
        query = query.where(Movement.part_id == part_id)
    if drawer_id is not None:
        query = query.where(Movement.drawer_id == drawer_id)
    query = query.order_by(Movement.created_at.desc(), Movement.id.desc()).limit(limit)

    return [
        MovementOut(
            id=m.id,
            part_id=m.part_id,
            part_name=p.name,
            drawer_id=m.drawer_id,
            drawer_label=d.label,
            delta=m.delta,
            resulting_quantity=m.resulting_quantity,
            reason=m.reason,
            created_at=m.created_at,
        )
        for m, p, d in session.exec(query).all()
    ]
