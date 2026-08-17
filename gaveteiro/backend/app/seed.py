"""Seed inicial: 12 módulos de 4x4 = 192 gavetas, no arranjo atual do usuário.

Arranjo físico (colunas 1..4, linhas 1..5):

    .   .   M3  M4
    .   .   M5  M6
    .   .   M7  M8
    .   .   M9  M10
    M1  M2  M11 M12

As gavetas são numeradas de 1 a 192 na ordem de leitura física, atravessando
os módulos que estão lado a lado (ver `numerar`).

O arranjo é editável depois pela tela de layout; isto é só o ponto de partida.
"""

from sqlmodel import Session, select

from .models import AppMeta, Category, Drawer, Module

SCHEMA_VERSION = "1"

# (nome, grid_col, grid_row)
DEFAULT_LAYOUT: list[tuple[str, int, int]] = [
    ("M3", 3, 1), ("M4", 4, 1),
    ("M5", 3, 2), ("M6", 4, 2),
    ("M7", 3, 3), ("M8", 4, 3),
    ("M9", 3, 4), ("M10", 4, 4),
    ("M1", 1, 5), ("M2", 2, 5), ("M11", 3, 5), ("M12", 4, 5),
]

DEFAULT_CATEGORIES: list[tuple[str, str]] = [
    ("Resistor", "#f59e0b"),
    ("Capacitor", "#3b82f6"),
    ("Indutor", "#8b5cf6"),
    ("Diodo", "#ef4444"),
    ("Transistor", "#10b981"),
    ("CI", "#06b6d4"),
    ("Conector", "#a855f7"),
    ("Módulo", "#ec4899"),
    ("Mecânica", "#78716c"),
    ("Outros", "#64748b"),
]

def ordem_natural(module: Module) -> tuple[int, str]:
    """Ordena M1, M2, … M10, M11, M12 — e não M1, M10, M11, M2 (alfabética).

    Módulos sem número no nome vão para o fim, em ordem alfabética.
    """
    digitos = "".join(ch for ch in module.name if ch.isdigit())
    return (int(digitos), "") if digitos else (10**9, module.name)


def _celulas(module: Module, ordem: str) -> list[tuple[int, int]]:
    """Posições de um módulo na ordem de leitura escolhida."""
    if ordem == "coluna":
        return [(row, col) for col in range(1, module.cols + 1) for row in range(1, module.rows + 1)]
    return [(row, col) for row in range(1, module.rows + 1) for col in range(1, module.cols + 1)]


def numerar(
    modules: list[Module],
    modo: str = "continuo",
    inicio: int = 1,
    ordem: str = "linha",
    prefixo: str = "",
) -> list[tuple[Module, int, int, str]]:
    """Gera os rótulos das gavetas. Devolve tuplas (módulo, linha, coluna, rótulo).

    modo:
      - "continuo": a contagem atravessa os módulos lado a lado. A linha de
        cima do M3 e a do M4 são lidas em sequência (1-4 no M3, 5-8 no M4)
        antes de descer para a linha seguinte.
      - "por_modulo": cada módulo recebe um bloco contínuo seguindo o número
        do módulo (M1 = 1-16, M2 = 17-32, … M12 = 177-192), independente de
        onde ele esteja no arranjo.
      - "pares": os módulos são tomados aos pares na ordem do número
        (M1/M2, M3/M4, …) e a linha atravessa os dois módulos do par, de modo
        que cada par consome 32 gavetas: M1/M2 = 1-32, M3/M4 = 33-64, etc.

    ordem: "linha" (esquerda→direita, cima→baixo) ou "coluna" (cima→baixo,
    coluna por coluna).

    prefixo: texto opcional antes do número, ex.: "G" gera G1, G2, G3…
    """
    if modo not in {"continuo", "por_modulo", "pares"}:
        raise ValueError(f"Modo desconhecido: {modo}")
    if ordem not in {"linha", "coluna"}:
        raise ValueError(f"Ordem desconhecida: {ordem}")

    resultado: list[tuple[Module, int, int, str]] = []
    numero = inicio

    if modo == "por_modulo":
        for module in sorted(modules, key=ordem_natural):
            for row, col in _celulas(module, ordem):
                resultado.append((module, row, col, f"{prefixo}{numero}"))
                numero += 1
        return resultado

    if modo == "pares":
        # Módulos aos pares na ordem do número (M1/M2, M3/M4, …), e dentro do
        # par a linha atravessa os dois: M1 leva 1-4 e o M2 continua em 5-8.
        # Independe de onde o par esteja no arranjo físico.
        naturais = sorted(modules, key=ordem_natural)
        for i in range(0, len(naturais), 2):
            par = naturais[i : i + 2]
            alturas = {m.rows for m in par}
            if len(alturas) != 1:
                raise ValueError(
                    f"O par {'/'.join(m.name for m in par)} tem alturas diferentes "
                    f"{alturas}; a numeração em pares exige mesma quantidade de linhas."
                )

            if ordem == "coluna":
                for module in par:
                    for col in range(1, module.cols + 1):
                        for row in range(1, module.rows + 1):
                            resultado.append((module, row, col, f"{prefixo}{numero}"))
                            numero += 1
            else:
                for row in range(1, par[0].rows + 1):
                    for module in par:
                        for col in range(1, module.cols + 1):
                            resultado.append((module, row, col, f"{prefixo}{numero}"))
                            numero += 1
        return resultado

    # Contínuo: percorre linha física de módulos por linha física de módulos.
    for grid_row in sorted({m.grid_row for m in modules}):
        na_linha = sorted((m for m in modules if m.grid_row == grid_row), key=lambda m: m.grid_col)
        alturas = {m.rows for m in na_linha}
        if len(alturas) != 1:
            raise ValueError(
                f"Módulos da linha {grid_row} têm alturas diferentes {alturas}; "
                "a numeração contínua exige mesma quantidade de linhas."
            )

        if ordem == "coluna":
            # Coluna por coluna, mas ainda atravessando os módulos da linha.
            for module in na_linha:
                for col in range(1, module.cols + 1):
                    for row in range(1, module.rows + 1):
                        resultado.append((module, row, col, f"{prefixo}{numero}"))
                        numero += 1
        else:
            for row in range(1, na_linha[0].rows + 1):
                for module in na_linha:
                    for col in range(1, module.cols + 1):
                        resultado.append((module, row, col, f"{prefixo}{numero}"))
                        numero += 1

    return resultado


def seed(session: Session) -> None:
    """Idempotente: só cria o que ainda não existe."""
    if session.exec(select(Module)).first() is None:
        modules = [
            Module(name=name, rows=4, cols=4, grid_col=grid_col, grid_row=grid_row)
            for name, grid_col, grid_row in DEFAULT_LAYOUT
        ]
        session.add_all(modules)
        session.flush()  # precisa dos ids para as gavetas

        for module, row, col, label in numerar(modules):
            session.add(Drawer(module_id=module.id, row=row, col=col, label=label))

    if session.exec(select(Category)).first() is None:
        for name, color in DEFAULT_CATEGORIES:
            session.add(Category(name=name, color=color))

    if session.get(AppMeta, "schema_version") is None:
        session.add(AppMeta(key="schema_version", value=SCHEMA_VERSION))

    session.commit()
