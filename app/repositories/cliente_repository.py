from app.database import get_connection
from app.models.cliente import Cliente


class ClienteRepository:
    def inserir(self, cliente: Cliente) -> Cliente:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO clientes (nome, numero, ativo)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (cliente.nome, cliente.numero, cliente.ativo),
                )
                cliente.id = cur.fetchone()[0]
            conn.commit()
        return cliente

    def listar_todos(self) -> list[Cliente]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, nome, numero, ativo
                    FROM clientes
                    WHERE ativo = TRUE
                    ORDER BY id
                    """
                )
                rows = cur.fetchall()

        return [Cliente(id=row[0], nome=row[1], numero=row[2], ativo=row[3]) for row in rows]

    def remover(self, cliente_id: int) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE clientes SET ativo = FALSE WHERE id = %s",
                    (cliente_id,),
                )
            conn.commit()
