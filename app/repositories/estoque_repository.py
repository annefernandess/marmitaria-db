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
