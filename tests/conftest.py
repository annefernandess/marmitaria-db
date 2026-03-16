from pathlib import Path

import psycopg2
import pytest

from app.database import DATABASE_URL

INIT_SQL = Path(__file__).parent.parent / "db" / "init.sql"


@pytest.fixture(scope="session", autouse=True)
def apply_schema():
    """Garante que as tabelas existem antes de qualquer teste da sessão."""
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(INIT_SQL.read_text())
    conn.close()


class _NoCommitConn:
    """
    Wrapper de conexão psycopg2 que suprime commits.

    Como psycopg2 é uma extensão C, seu atributo `commit` é read-only e não
    pode ser substituído diretamente. Este wrapper intercepta todas as chamadas
    e transforma commits em no-ops, permitindo que o fixture faça rollback de
    tudo ao final do teste e deixe o banco limpo.
    """

    def __init__(self, conn):
        self._conn = conn

    def commit(self):
        pass  # no-op: o rollback no teardown do fixture desfaz tudo

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._conn.rollback()
        return False


@pytest.fixture
def db(monkeypatch):
    """
    Fornece uma conexão real com o banco para cada teste.

    Todos os inserts e updates executam de verdade (cursores retornam IDs, etc.)
    mas nenhum commit é persistido. Ao final do teste, a transação é revertida —
    deixando o banco exatamente como estava antes.
    """
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    wrapped = _NoCommitConn(conn)

    with conn.cursor() as cur:
        cur.execute(
            """
            TRUNCATE TABLE
                pedido_itens,
                pedidos,
                usuarios,
                clientes,
                estoque
            RESTART IDENTITY CASCADE
            """
        )
        cur.execute(
            """
            INSERT INTO usuarios (nome, email, senha, numero, role, cliente_id, ativo)
            VALUES ('YAO Admin', 'yao@lanches.com', 'admin', '00000000000', 'admin', NULL, TRUE)
            """
        )

    mock = lambda: wrapped  # noqa: E731
    monkeypatch.setattr("app.repositories.cliente_repository.get_connection", mock)
    monkeypatch.setattr("app.repositories.estoque_repository.get_connection", mock)
    monkeypatch.setattr("app.repositories.pedido_repository.get_connection", mock)
    monkeypatch.setattr("app.repositories.pedido_item_repository.get_connection", mock)
    monkeypatch.setattr("app.repositories.usuario_repository.get_connection", mock)

    yield wrapped

    conn.rollback()
    conn.close()
