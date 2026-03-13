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
