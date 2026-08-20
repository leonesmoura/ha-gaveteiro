"""Peças, categorias e imagens."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session, select

from .. import images
from ..db import get_session
from ..models import Category, Part, PartTag, Stock
from ..queries import part_out
from ..schemas import CategoryIn, CategoryOut, PartIn, PartOut, PartUpdate

router = APIRouter()


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(session: Session = Depends(get_session)):
    return session.exec(select(Category).order_by(Category.name)).all()


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(payload: CategoryIn, session: Session = Depends(get_session)):
    existing = session.exec(select(Category).where(Category.name == payload.name)).first()
    if existing:
        raise HTTPException(409, "Categoria já existe")
    category = Category(**payload.model_dump())
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.get("/parts", response_model=list[PartOut])
def list_parts(session: Session = Depends(get_session)):
    parts = session.exec(select(Part).order_by(Part.name)).all()
    return [part_out(session, p) for p in parts]


@router.get("/parts/low-stock", response_model=list[PartOut])
def low_stock(session: Session = Depends(get_session)):
    """Peças cuja soma em todas as gavetas está abaixo do mínimo."""
    parts = session.exec(select(Part).where(Part.min_qty > 0)).all()
    return [out for out in (part_out(session, p) for p in parts) if out.low_stock]


@router.get("/parts/{part_id}", response_model=PartOut)
def get_part(part_id: int, session: Session = Depends(get_session)):
    part = session.get(Part, part_id)
    if part is None:
        raise HTTPException(404, "Peça não encontrada")
    return part_out(session, part)


@router.post("/parts", response_model=PartOut, status_code=201)
def create_part(payload: PartIn, session: Session = Depends(get_session)):
    part = Part(**payload.model_dump())
    session.add(part)
    session.commit()
    session.refresh(part)
    return part_out(session, part)


@router.patch("/parts/{part_id}", response_model=PartOut)
def update_part(part_id: int, payload: PartUpdate, session: Session = Depends(get_session)):
    part = session.get(Part, part_id)
    if part is None:
        raise HTTPException(404, "Peça não encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(part, field, value)
    session.add(part)
    session.commit()
    session.refresh(part)
    return part_out(session, part)


@router.delete("/parts/{part_id}", status_code=204)
def delete_part(part_id: int, session: Session = Depends(get_session)):
    part = session.get(Part, part_id)
    if part is None:
        raise HTTPException(404, "Peça não encontrada")

    # Remove o estoque junto; o histórico (Movement) fica para consulta.
    for stock in session.exec(select(Stock).where(Stock.part_id == part_id)).all():
        session.delete(stock)
    for link in session.exec(select(PartTag).where(PartTag.part_id == part_id)).all():
        session.delete(link)

    images.remover(part.image_path)

    session.delete(part)
    session.commit()


@router.post("/parts/{part_id}/image", response_model=PartOut)
async def upload_image(
    part_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    part = session.get(Part, part_id)
    if part is None:
        raise HTTPException(404, "Peça não encontrada")

    antiga = part.image_path
    part.image_path = images.salvar(file)
    session.add(part)
    session.commit()
    session.refresh(part)

    images.remover(antiga)
    return part_out(session, part)
