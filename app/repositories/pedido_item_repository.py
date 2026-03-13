from app.database import get_connection
from app.models.pedido_item import PedidoItem


class PedidoItemRepository:
    def listar_todos(self) -> list[PedidoItem]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, pedido_id, item_id, quantidade
                    FROM pedido_itens
                    ORDER BY id
                    """
                )
                rows = cur.fetchall()

        return [
            PedidoItem(
                id=row[0],
                pedido_id=row[1],
                item_id=row[2],
                quantidade=row[3],
            )
            for row in rows
        ]

    def remover(self, pedido_item_id: int) -> None:
        """Remove um item de pedido e restaura o estoque correspondente."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT item_id, quantidade FROM pedido_itens WHERE id = %s",
                    (pedido_item_id,),
                )
                row = cur.fetchone()

                if row is None:
                    conn.commit()
                    return

                item_id, quantidade = row

                cur.execute(
                    """
                    UPDATE estoque
                    SET quantidade_disponivel = quantidade_disponivel + %s
                    WHERE id = %s
                    """,
                    (quantidade, item_id),
                )

                cur.execute("DELETE FROM pedido_itens WHERE id = %s", (pedido_item_id,))

            conn.commit()
