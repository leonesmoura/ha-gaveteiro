"""Schemas de entrada/saída da API (separados das tabelas)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ModuleOut(BaseModel):
    id: int
    name: str
    rows: int
    cols: int
    grid_col: int
    grid_row: int


class ModuleUpdate(BaseModel):
    name: Optional[str] = None
    grid_col: Optional[int] = None
    grid_row: Optional[int] = None


class ModuleCreate(BaseModel):
    name: str
    rows: int = 4
    cols: int = 4
    grid_col: int = 1
    grid_row: int = 1
    """Rótulos das novas gavetas; se omitido, continuam a numeração existente."""
    label_prefix: str = ""


class ModuleLayoutItem(BaseModel):
    id: int
    grid_col: int
    grid_row: int
    name: Optional[str] = None


class ModuleLayoutIn(BaseModel):
    """Arranjo completo dos módulos, aplicado de uma vez só."""

    modules: list[ModuleLayoutItem]


class DrawerRename(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None


class RenumberIn(BaseModel):
    """Refaz os rótulos de todas as gavetas."""

    modo: str = "continuo"  # continuo | por_modulo
    inicio: int = 1
    ordem: str = "linha"  # linha | coluna
    prefixo: str = ""


class CategoryOut(BaseModel):
    id: int
    name: str
    color: str


class CategoryIn(BaseModel):
    name: str
    color: str = "#64748b"


class PartIn(BaseModel):
    name: str
    description: str = ""
    category_id: Optional[int] = None
    package: str = ""
    value: str = ""
    manufacturer_code: str = ""
    datasheet_url: str = ""
    min_qty: int = 0
    notes: str = ""


class PartUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    package: Optional[str] = None
    value: Optional[str] = None
    manufacturer_code: Optional[str] = None
    datasheet_url: Optional[str] = None
    min_qty: Optional[int] = None
    notes: Optional[str] = None


class PartOut(BaseModel):
    id: int
    name: str
    description: str
    category_id: Optional[int]
    category_name: Optional[str] = None
    category_color: Optional[str] = None
    package: str
    value: str
    manufacturer_code: str
    image_path: Optional[str]
    datasheet_url: str
    min_qty: int
    notes: str
    total_quantity: int = 0
    drawer_labels: list[str] = []
    low_stock: bool = False


class StockEntryOut(BaseModel):
    part: PartOut
    quantity: int


class DrawerOut(BaseModel):
    id: int
    module_id: int
    module_name: str
    row: int
    col: int
    label: str
    description: str = ""
    total_quantity: int = 0
    part_count: int = 0
    low_stock: bool = False
    primary_color: Optional[str] = None


class DrawerDetail(DrawerOut):
    entries: list[StockEntryOut] = []


class StockAssign(BaseModel):
    """Coloca uma peça numa gaveta com uma quantidade inicial."""

    part_id: int
    quantity: int = 0


class StockAdjust(BaseModel):
    """Ajuste relativo (delta) ou absoluto (set_to). Um dos dois."""

    delta: Optional[int] = None
    set_to: Optional[int] = None
    reason: str = ""


class MovementOut(BaseModel):
    id: int
    part_id: int
    part_name: str
    drawer_id: int
    drawer_label: str
    delta: int
    resulting_quantity: int
    reason: str
    created_at: datetime


class SearchResult(BaseModel):
    parts: list[PartOut]
    drawer_ids: list[int]


class ImportItem(BaseModel):
    name: str
    value: str = ""
    package: str = ""
    quantity: int = 0
    category: str = ""
    notes: str = ""


class ImportDrawer(BaseModel):
    label: str = ""
    description: str = ""
    items: list[ImportItem] = []


class ImportModule(BaseModel):
    name: str
    rows: int = 1
    cols: int = 1
    grid_col: int = 1
    grid_row: int = 1
    drawers: list[ImportDrawer] = []


class ImportIn(BaseModel):
    drawers: list[ImportDrawer] = []
    new_modules: list[ImportModule] = []


class ImportResult(BaseModel):
    parts_created: int
    descriptions_set: int
    modules_created: int
    skipped: list[str]


class LoginIn(BaseModel):
    username: str
    password: str


class AuthStatus(BaseModel):
    authenticated: bool
    via_ingress: bool
    username: Optional[str] = None
