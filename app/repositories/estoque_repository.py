from app.database import get_connection
from app.models.estoque import Estoque


class EstoqueRepository:
    def inserir(self, estoque: Estoque) -> Estoque:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO estoque (item, quantidade_disponivel, valor)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (estoque.item, estoque.quantidade_disponivel, estoque.valor),
                )
                estoque.id = cur.fetchone()[0]
            conn.commit()
        return estoque

    def listar_todos(self) -> list[Estoque]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, item, quantidade_disponivel, valor
                    FROM estoque
                    ORDER BY id
                    """
                )
                rows = cur.fetchall()

        return [
            Estoque(
                id=row[0],
                item=row[1],
                quantidade_disponivel=row[2],
                valor=row[3],
            )
            for row in rows
        ]

    def remover(self, item_id: int) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM estoque WHERE id = %s", (item_id,))
            conn.commit()
