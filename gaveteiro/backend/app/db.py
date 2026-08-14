"""Engine SQLite e sessão."""

from collections.abc import Iterator

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from . import config

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        config.ensure_dirs()
        _engine = create_engine(
            f"sqlite:///{config.DB_PATH}",
            connect_args={"check_same_thread": False},
        )

        # WAL permite o add-on SQLite Web ler enquanto o app escreve.
        @event.listens_for(_engine, "connect")
        def _set_pragmas(dbapi_conn, _record):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

    return _engine


def init_db() -> None:
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    _migrar_colunas(engine)


# Colunas adicionadas depois da v1. create_all() só cria tabelas que não
# existem — não altera as existentes —, então bancos antigos precisam do
# ALTER TABLE explícito.
COLUNAS_NOVAS: list[tuple[str, str, str]] = [
    ("drawer", "description", "TEXT NOT NULL DEFAULT ''"),
]


def _migrar_colunas(engine) -> None:
    from sqlalchemy import text

    with engine.begin() as conn:
        for tabela, coluna, definicao in COLUNAS_NOVAS:
            existentes = {
                linha[1] for linha in conn.exec_driver_sql(f"PRAGMA table_info({tabela})")
            }
            if not existentes:
                continue  # tabela ainda não existe; create_all cuida dela
            if coluna not in existentes:
                conn.execute(text(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}"))


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
