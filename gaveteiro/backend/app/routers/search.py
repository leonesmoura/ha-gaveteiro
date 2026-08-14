"""Busca — o caso de uso principal: "onde está meu 10k 0805?"

Devolve as peças e os ids das gavetas para o frontend destacar no grid.
"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, col, or_, select

from ..db import get_session
from ..models import Category, Part, Stock
from ..queries import part_out
from ..schemas import SearchResult

router = APIRouter()


@router.get("/search", response_model=SearchResult)
def search(
    q: str = Query(default="", description="Texto livre: nome, valor, package, código"),
    category_id: int | None = None,
    session: Session = Depends(get_session),
):
    query = select(Part)

    term = q.strip()
    if term:
        like = f"%{term}%"
        query = query.where(
            or_(
                col(Part.name).ilike(like),
                col(Part.value).ilike(like),
                col(Part.package).ilike(like),
                col(Part.manufacturer_code).ilike(like),
                col(Part.description).ilike(like),
                col(Part.notes).ilike(like),
            )
        )
    if category_id is not None:
        query = query.where(Part.category_id == category_id)

    parts = session.exec(query.order_by(Part.name)).all()
    if not parts:
        return SearchResult(parts=[], drawer_ids=[])

    categories = {c.id: c for c in session.exec(select(Category)).all()}
    part_ids = [p.id for p in parts]
    drawer_ids = session.exec(
        select(Stock.drawer_id).where(col(Stock.part_id).in_(part_ids)).distinct()
    ).all()

    return SearchResult(
        parts=[part_out(session, p, categories) for p in parts],
        drawer_ids=sorted(drawer_ids),
    )
