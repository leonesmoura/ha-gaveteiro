"""Importa a planilha Estoque.xlsx para o Gaveteiro.

A planilha é um desenho do gaveteiro: blocos de 8 gavetas, e para cada gaveta
uma coluna de quantidade e uma de item.

    linha r      | 1 |  | 2 |  | 3 | ...     <- número da gaveta
    linha r+1    | Resistores 1 |  | ...     <- nome da gaveta
    linha r+2..  |   | 1 |   | 1.1 | ...     <- itens (qtd na par, item na ímpar)

Quando a coluna de quantidade está vazia, o item é registrado com quantidade 0
— é o caso dos resistores, cujas quantidades o usuário confere depois.

Uso:
    python import_xlsx.py planilha.xlsx --url http://IP:8099 --user admin --password X
    python import_xlsx.py planilha.xlsx --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from dataclasses import dataclass, field

GAVETAS_POR_BLOCO = 8

# Palavra-chave no nome da gaveta -> categoria. A primeira que casar vence,
# então as mais específicas vêm antes.
CATEGORIAS: list[tuple[str, str]] = [
    ("resistor", "Resistor"),
    ("trimpot", "Resistor"),
    ("trimmer", "Capacitor"),
    ("varistor", "Resistor"),
    ("ntc", "Resistor"),
    ("cap.", "Capacitor"),
    ("capacitor", "Capacitor"),
    ("indutor", "Indutor"),
    ("led", "Diodo"),
    ("diodo", "Diodo"),
    ("zener", "Diodo"),
    ("retificador", "Diodo"),
    ("diac", "Diodo"),
    ("triac", "Transistor"),
    ("scr", "Transistor"),
    ("igbt", "Transistor"),
    ("bjt", "Transistor"),
    ("mosfet", "Transistor"),
    ("jfet", "Transistor"),
    ("ampop", "CI"),
    ("pic", "CI"),
    ("eprom", "CI"),
    ("regulador", "CI"),
    ("optcoacoplador", "CI"),
    ("optoacoplador", "CI"),
    ("receptor ir", "CI"),
    ("fotodiac", "CI"),
    ("conector", "Conector"),
    ("display", "Módulo"),
    ("cristal", "Outros"),
    ("chave", "Mecânica"),
]


def categoria_de(nome_gaveta: str) -> str:
    alvo = nome_gaveta.lower()
    for chave, categoria in CATEGORIAS:
        if chave in alvo:
            return categoria
    return "Outros"


@dataclass
class Item:
    texto: str
    quantidade: int


@dataclass
class GavetaImportada:
    numero: int
    nome: str
    itens: list[Item] = field(default_factory=list)


@dataclass
class GavetaExtra:
    """A planilha tem uma área à direita (Gaveta1/2/3) que não pertence ao
    gaveteiro de 192 — é outro organizador."""

    titulo: str
    nome: str
    itens: list[Item] = field(default_factory=list)


# Colunas onde começa cada gaveta da área extra.
COLUNAS_EXTRAS = (18, 22, 26)


def ler_extras(linhas: list[list[str]]) -> list[GavetaExtra]:
    extras: list[GavetaExtra] = []
    for col in COLUNAS_EXTRAS:
        titulo = _celula(linhas[0], col) if linhas else ""
        if not titulo:
            continue
        nome = _celula(linhas[1], col) if len(linhas) > 1 else ""
        itens = []
        for linha in linhas[2:]:
            item_txt = _celula(linha, col + 1)
            if item_txt:
                itens.append(Item(item_txt, _inteiro(_celula(linha, col))))
        extras.append(GavetaExtra(titulo, nome, itens))
    return extras


def ler_linhas(caminho: str) -> list[list[str]]:
    import openpyxl

    ws = openpyxl.load_workbook(caminho, data_only=True)["Planilha1"]
    return [
        ["" if c is None else str(c).strip() for c in linha]
        for linha in ws.iter_rows(values_only=True)
    ]


def ler_planilha(linhas: list[list[str]]) -> list[GavetaImportada]:

    gavetas: list[GavetaImportada] = []
    i = 0
    while i < len(linhas):
        numeros = _linha_de_numeros(linhas[i])
        if numeros is None:
            i += 1
            continue

        nomes = linhas[i + 1] if i + 1 < len(linhas) else []
        bloco = {
            pos: GavetaImportada(numero=num, nome=_celula(nomes, pos * 2))
            for pos, num in numeros.items()
        }

        # Conteúdo vai até o próximo cabeçalho de bloco.
        j = i + 2
        while j < len(linhas) and _linha_de_numeros(linhas[j]) is None:
            for pos, gaveta in bloco.items():
                qtd_txt = _celula(linhas[j], pos * 2)
                item_txt = _celula(linhas[j], pos * 2 + 1)
                if item_txt:
                    gaveta.itens.append(Item(item_txt, _inteiro(qtd_txt)))
            j += 1

        gavetas.extend(g for g in bloco.values() if g.nome or g.itens)
        i = j

    return gavetas


def _celula(linha: list[str], idx: int) -> str:
    return linha[idx] if idx < len(linha) else ""


def _inteiro(texto: str) -> int:
    try:
        return int(float(texto))
    except (TypeError, ValueError):
        return 0


def _linha_de_numeros(linha: list[str]) -> dict[int, int] | None:
    """Cabeçalho de bloco: números de gaveta nas colunas pares 0,2,4…14."""
    achados: dict[int, int] = {}
    for pos in range(GAVETAS_POR_BLOCO):
        valor = _celula(linha, pos * 2)
        if re.fullmatch(r"\d{1,3}", valor):
            achados[pos] = int(valor)

    if len(achados) < GAVETAS_POR_BLOCO:
        return None
    # Números de gaveta são consecutivos; uma linha de valores como
    # "1, 10, 100" não é cabeçalho.
    ordenados = [achados[p] for p in sorted(achados)]
    if ordenados != list(range(ordenados[0], ordenados[0] + GAVETAS_POR_BLOCO)):
        return None
    return achados


# --- envio para a API ------------------------------------------------------


class Cliente:
    def __init__(self, url: str, user: str, password: str) -> None:
        self.url = url.rstrip("/")
        self.cookie = ""
        self._login(user, password)

    def _request(self, metodo: str, caminho: str, corpo: dict | None = None) -> object:
        dados = json.dumps(corpo).encode() if corpo is not None else None
        req = urllib.request.Request(f"{self.url}/api{caminho}", data=dados, method=metodo)
        req.add_header("Content-Type", "application/json")
        if self.cookie:
            req.add_header("Cookie", self.cookie)
        with urllib.request.urlopen(req) as resp:
            if "Set-Cookie" in resp.headers:
                self.cookie = resp.headers["Set-Cookie"].split(";")[0]
            texto = resp.read().decode()
            return json.loads(texto) if texto else None

    def _login(self, user: str, password: str) -> None:
        self._request("POST", "/auth/login", {"username": user, "password": password})

    def get(self, caminho: str) -> object:
        return self._request("GET", caminho)

    def post(self, caminho: str, corpo: dict) -> object:
        return self._request("POST", caminho, corpo)

    def patch(self, caminho: str, corpo: dict) -> object:
        return self._request("PATCH", caminho, corpo)


class Importador:
    def __init__(self, cliente: Cliente) -> None:
        self.cliente = cliente
        self.categorias = {c["name"]: c["id"] for c in cliente.get("/categories")}
        self.pecas = 0
        self.descricoes = 0
        self.avisos: list[str] = []

    def _categoria_id(self, base: str) -> int:
        nome = categoria_de(base)
        if nome not in self.categorias:
            nova = self.cliente.post("/categories", {"name": nome, "color": "#64748b"})
            self.categorias[nome] = nova["id"]
        return self.categorias[nome]

    def preencher(self, drawer_id: int, base: str, itens: list[Item], origem: str) -> None:
        if base:
            self.cliente.patch(f"/drawers/{drawer_id}", {"description": base})
            self.descricoes += 1

        categoria_id = self._categoria_id(base)
        for item in itens:
            peca = self.cliente.post(
                "/parts",
                {
                    "name": f"{base} {item.texto}".strip(),
                    "value": item.texto,
                    "category_id": categoria_id,
                    "notes": f"Importado da planilha ({origem})",
                },
            )
            self.pecas += 1
            self.cliente.post(
                f"/drawers/{drawer_id}/stock",
                {"part_id": peca["id"], "quantity": item.quantidade},
            )

    def gaveteiro_principal(self, gavetas: list[GavetaImportada]) -> None:
        por_rotulo = {d["label"]: d["id"] for d in self.cliente.get("/drawers")}
        for gaveta in gavetas:
            drawer_id = por_rotulo.get(str(gaveta.numero))
            if drawer_id is None:
                self.avisos.append(f"Gaveta {gaveta.numero} não existe no app — ignorada")
                continue
            self.preencher(drawer_id, gaveta.nome, gaveta.itens, f"gaveta {gaveta.numero}")

    def modulo_extra(self, extras: list[GavetaExtra], nome_modulo: str) -> None:
        """Cria um módulo separado para a área Gaveta1/2/3 da planilha."""
        if not extras:
            return

        modulos = self.cliente.get("/modules")
        if any(m["name"] == nome_modulo for m in modulos):
            self.avisos.append(f"Módulo {nome_modulo} já existe — área extra não importada")
            return

        ocupadas = {(m["grid_col"], m["grid_row"]) for m in modulos}
        posicao = next(
            ((c, r) for r in range(1, 30) for c in range(1, 30) if (c, r) not in ocupadas),
            (1, 1),
        )

        modulo = self.cliente.post(
            "/modules",
            {
                "name": nome_modulo,
                "rows": 1,
                "cols": len(extras),
                "grid_col": posicao[0],
                "grid_row": posicao[1],
            },
        )
        novas = sorted(
            (d for d in self.cliente.get("/drawers") if d["module_id"] == modulo["id"]),
            key=lambda d: d["col"],
        )
        for gaveta, extra in zip(novas, extras):
            self.preencher(gaveta["id"], extra.nome, extra.itens, extra.titulo)


def montar_plano(gavetas: list[GavetaImportada], extras: list[GavetaExtra], args) -> dict:
    """Formato aceito por POST /api/import."""

    def itens(base: str, lista: list[Item], origem: str) -> list[dict]:
        categoria = categoria_de(base)
        return [
            {
                "name": f"{base} {item.texto}".strip(),
                "value": item.texto,
                "quantity": item.quantidade,
                "category": categoria,
                "notes": f"Importado da planilha ({origem})",
            }
            for item in lista
        ]

    plano: dict = {
        "drawers": [
            {
                "label": str(g.numero),
                "description": g.nome,
                "items": itens(g.nome, g.itens, f"gaveta {g.numero}"),
            }
            for g in gavetas
        ],
        "new_modules": [],
    }

    if extras:
        plano["new_modules"].append(
            {
                "name": args.modulo_extra,
                "rows": 1,
                "cols": len(extras),
                "grid_col": args.extra_col,
                "grid_row": args.extra_row,
                "drawers": [
                    {
                        "description": e.nome,
                        "items": itens(e.nome, e.itens, e.titulo),
                    }
                    for e in extras
                ],
            }
        )

    return plano


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("planilha")
    parser.add_argument("--url", default="http://127.0.0.1:8099")
    parser.add_argument("--user", default="admin")
    parser.add_argument("--password", default="")
    parser.add_argument("--dry-run", action="store_true", help="só mostra o que seria criado")
    parser.add_argument("--modulo-extra", default="Extras", help="nome do módulo da área Gaveta1/2/3")
    parser.add_argument("--emit-json", help="grava o plano num arquivo para POST /api/import")
    parser.add_argument("--extra-col", type=int, default=1, help="coluna do módulo extra no arranjo")
    parser.add_argument("--extra-row", type=int, default=1, help="linha do módulo extra no arranjo")
    args = parser.parse_args()

    linhas = ler_linhas(args.planilha)
    gavetas = ler_planilha(linhas)
    extras = ler_extras(linhas)

    total_itens = sum(len(g.itens) for g in gavetas) + sum(len(e.itens) for e in extras)
    com_qtd = sum(1 for g in gavetas for i in g.itens if i.quantidade > 0)
    com_qtd += sum(1 for e in extras for i in e.itens if i.quantidade > 0)

    print(f"Gavetas com conteúdo: {len(gavetas)} (+{len(extras)} na área extra)")
    print(f"Itens: {total_itens} ({com_qtd} com quantidade, {total_itens - com_qtd} a confirmar)")

    if args.dry_run:
        for gaveta in gavetas:
            itens = ", ".join(
                f"{i.texto}({i.quantidade})" if i.quantidade else i.texto for i in gaveta.itens
            )
            print(f"  {gaveta.numero:>3} {gaveta.nome:<28} [{categoria_de(gaveta.nome)}] {itens}")
        for extra in extras:
            itens = ", ".join(f"{i.texto}({i.quantidade})" for i in extra.itens)
            print(f"  {extra.titulo:>3} {extra.nome:<28} [{categoria_de(extra.nome)}] {itens}")
        return 0

    if args.emit_json:
        plano = montar_plano(gavetas, extras, args)
        with open(args.emit_json, "w", encoding="utf-8") as saida:
            json.dump(plano, saida, ensure_ascii=False)
        print(f"Plano gravado em {args.emit_json}")
        return 0

    importador = Importador(Cliente(args.url, args.user, args.password))
    importador.gaveteiro_principal(gavetas)
    importador.modulo_extra(extras, args.modulo_extra)

    print(f"Criadas {importador.pecas} peças e {importador.descricoes} descrições de gaveta.")
    for aviso in importador.avisos:
        print(f"  aviso: {aviso}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
