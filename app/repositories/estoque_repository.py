from app.database import get_connection
from app.models.estoque import Estoque


class EstoqueRepository:
    def inserir(self, estoque: Estoque) -> Estoque:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO estoque (item, quantidade_disponivel, valor, ativo)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        estoque.item,
                        estoque.quantidade_disponivel,
                        estoque.valor,
                        estoque.ativo,
                    ),
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
                    WHERE ativo = TRUE
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

    def exibir_um(self, item_id: int) -> Estoque | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, item, quantidade_disponivel, valor, ativo
                    FROM estoque
                    WHERE id = %s
                    """,
                    (item_id,),
                )
                row = cur.fetchone()

        if row is None or row[4] is not True:
            return None

        return Estoque(
            id=row[0],
            item=row[1],
            quantidade_disponivel=row[2],
            valor=row[3],
            ativo=row[4],
        )

    def buscar_por_nome(self, termo: str) -> list[Estoque]:
        like = f"%{termo}%"
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, item, quantidade_disponivel, valor, ativo
                    FROM estoque
                    WHERE ativo = TRUE AND item ILIKE %s
                    ORDER BY id
                    """,
                    (like,),
                )
                rows = cur.fetchall()

        return [
            Estoque(
                id=row[0],
                item=row[1],
                quantidade_disponivel=row[2],
                valor=row[3],
                ativo=row[4],
            )
            for row in rows
        ]

    def alterar(self, estoque: Estoque) -> Estoque:
        if estoque.id is None:
            raise ValueError("ID do estoque é obrigatório para alterar.")

        if estoque.quantidade_disponivel < 0:
            raise ValueError("Quantidade disponível não pode ser negativa.")

        if estoque.valor <= 0:
            raise ValueError("Valor do item deve ser maior que zero.")

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE estoque
                    SET item = %s, quantidade_disponivel = %s, valor = %s
                    WHERE id = %s AND ativo = TRUE
                    RETURNING id
                    """,
                    (
                        estoque.item,
                        estoque.quantidade_disponivel,
                        estoque.valor,
                        estoque.id,
                    ),
                )
                updated = cur.fetchone()
            conn.commit()

        if updated is None:
            raise ValueError("Item de estoque não encontrado ou inativo.")

        return estoque

    def remover(self, item_id: int) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE estoque SET ativo = FALSE WHERE id = %s",
                    (item_id,),
                )
            conn.commit()
