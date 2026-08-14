"""Modelo de dados do gaveteiro.

Um gaveteiro é feito de módulos; cada módulo tem uma grade de gavetas
(4x4 no caso atual). Uma gaveta pode conter mais de uma peça, então o
estoque é a tabela associativa Stock. Todo ajuste de quantidade gera um
Movement, que é o histórico.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Module(SQLModel, table=True):
    """Um bloco físico de gavetas, posicionado no canvas do dashboard."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    rows: int = 4
    cols: int = 4
    # Posição do módulo no arranjo da parede/bancada (1-indexado).
    grid_col: int = 1
    grid_row: int = 1

    drawers: list["Drawer"] = Relationship(back_populates="module")


class Drawer(SQLModel, table=True):
    """Uma gaveta. row/col são 1-indexados dentro do módulo."""

    id: Optional[int] = Field(default=None, primary_key=True)
    module_id: int = Field(foreign_key="module.id", index=True)
    row: int
    col: int
    label: str = Field(index=True, unique=True)
    # Para que serve a gaveta ("Cap. Poliester"), independente do que há nela.
    description: str = ""

    module: Optional[Module] = Relationship(back_populates="drawers")
    stock: list["Stock"] = Relationship(back_populates="drawer")


class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    color: str = "#64748b"


class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)


class PartTag(SQLModel, table=True):
    part_id: int = Field(foreign_key="part.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)


class Part(SQLModel, table=True):
    """Um componente. `value` e `package` são o que se busca no dia a dia."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    category_id: Optional[int] = Field(default=None, foreign_key="category.id", index=True)
    package: str = Field(default="", index=True)
    value: str = Field(default="", index=True)
    manufacturer_code: str = Field(default="", index=True)
    image_path: Optional[str] = None
    datasheet_url: str = ""
    min_qty: int = 0
    notes: str = ""
    created_at: datetime = Field(default_factory=utcnow)

    stock: list["Stock"] = Relationship(back_populates="part")


class Stock(SQLModel, table=True):
    """Quantidade de uma peça numa gaveta específica."""

    drawer_id: int = Field(foreign_key="drawer.id", primary_key=True)
    part_id: int = Field(foreign_key="part.id", primary_key=True)
    quantity: int = 0

    drawer: Optional[Drawer] = Relationship(back_populates="stock")
    part: Optional[Part] = Relationship(back_populates="stock")


class Movement(SQLModel, table=True):
    """Histórico: uma linha por ajuste de quantidade."""

    id: Optional[int] = Field(default=None, primary_key=True)
    part_id: int = Field(foreign_key="part.id", index=True)
    drawer_id: int = Field(foreign_key="drawer.id", index=True)
    delta: int
    resulting_quantity: int
    reason: str = ""
    created_at: datetime = Field(default_factory=utcnow, index=True)


class AppMeta(SQLModel, table=True):
    """Chave/valor para versão de schema e afins."""

    key: str = Field(primary_key=True)
    value: str = ""
