from app.database import get_connection
from app.models.cliente import Cliente


class ClienteRepository:
    def inserir(self, cliente: Cliente) -> Cliente:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO clientes (nome, numero) VALUES (%s, %s) RETURNING id",
                    (cliente.nome, cliente.numero),
                )
                cliente.id = cur.fetchone()[0]
            conn.commit()
        return cliente

    def listar_todos(self) -> list[Cliente]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, nome, numero FROM clientes ORDER BY id")
                rows = cur.fetchall()

        return [Cliente(id=row[0], nome=row[1], numero=row[2]) for row in rows]

    def remover(self, cliente_id: int) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM clientes WHERE id = %s", (cliente_id,))
            conn.commit()
