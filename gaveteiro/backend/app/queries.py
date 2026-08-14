"""Montagem dos objetos de saída a partir das tabelas.

Centralizado aqui porque tanto a listagem de gavetas quanto a busca e o
detalhe precisam dos mesmos totais (quantidade, estoque baixo, cor).
"""

from typing import Optional

from sqlmodel import Session, select

from .models import Category, Drawer, Module, Part, Stock
from .schemas import DrawerOut, PartOut, StockEntryOut


def _categories(session: Session) -> dict[int, Category]:
    return {c.id: c for c in session.exec(select(Category)).all()}


def part_out(
    session: Session,
    part: Part,
    categories: Optional[dict[int, Category]] = None,
) -> PartOut:
    categories = categories if categories is not None else _categories(session)
    rows = session.exec(
        select(Stock, Drawer).join(Drawer, Drawer.id == Stock.drawer_id).where(Stock.part_id == part.id)
    ).all()
    total = sum(s.quantity for s, _ in rows)
    category = categories.get(part.category_id) if part.category_id else None
    return PartOut(
        id=part.id,
        name=part.name,
        description=part.description,
        category_id=part.category_id,
        category_name=category.name if category else None,
        category_color=category.color if category else None,
        package=part.package,
        value=part.value,
        manufacturer_code=part.manufacturer_code,
        image_path=part.image_path,
        datasheet_url=part.datasheet_url,
        min_qty=part.min_qty,
        notes=part.notes,
        total_quantity=total,
        drawer_labels=sorted(d.label for _, d in rows),
        low_stock=part.min_qty > 0 and total < part.min_qty,
    )


def drawer_summaries(session: Session) -> list[DrawerOut]:
    """Todas as gavetas com seus totais — é o que o grid consome."""
    modules = {m.id: m for m in session.exec(select(Module)).all()}
    categories = _categories(session)
    drawers = session.exec(select(Drawer)).all()

    stock_rows = session.exec(select(Stock, Part).join(Part, Part.id == Stock.part_id)).all()
    by_drawer: dict[int, list[tuple[Stock, Part]]] = {}
    for stock, part in stock_rows:
        by_drawer.setdefault(stock.drawer_id, []).append((stock, part))

    out: list[DrawerOut] = []
    for drawer in drawers:
        entries = by_drawer.get(drawer.id, [])
        total = sum(s.quantity for s, _ in entries)
        low = any(p.min_qty > 0 and s.quantity < p.min_qty for s, p in entries)
        color = None
        if entries:
            first_category = next(
                (categories.get(p.category_id) for _, p in entries if p.category_id in categories),
                None,
            )
            color = first_category.color if first_category else None
        out.append(
            DrawerOut(
                id=drawer.id,
                module_id=drawer.module_id,
                module_name=modules[drawer.module_id].name,
                row=drawer.row,
                col=drawer.col,
                label=drawer.label,
                total_quantity=total,
                part_count=len(entries),
                low_stock=low,
                primary_color=color,
            )
        )
    return out


def drawer_entries(session: Session, drawer: Drawer) -> list[StockEntryOut]:
    categories = _categories(session)
    rows = session.exec(
        select(Stock, Part).join(Part, Part.id == Stock.part_id).where(Stock.drawer_id == drawer.id)
    ).all()
    return [
        StockEntryOut(part=part_out(session, part, categories), quantity=stock.quantity)
        for stock, part in rows
    ]
