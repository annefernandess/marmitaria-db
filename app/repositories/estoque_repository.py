from decimal import Decimal

from app.database import get_connection
from app.models.estoque import Estoque


class EstoqueRepository:
    def inserir(self, estoque: Estoque) -> Estoque:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO estoque (item, quantidade_disponivel, valor, categoria, fabricado_em_mari, ativo)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        estoque.item,
                        estoque.quantidade_disponivel,
                        estoque.valor,
                        estoque.categoria,
                        estoque.fabricado_em_mari,
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
                    SELECT id, item, quantidade_disponivel, valor, categoria, fabricado_em_mari, ativo
                    FROM estoque
                    WHERE ativo = TRUE
                    ORDER BY id
                    """
                )
                rows = cur.fetchall()

        return [
            Estoque(id=r[0], item=r[1], quantidade_disponivel=r[2], valor=r[3], categoria=r[4], fabricado_em_mari=r[5], ativo=r[6])
            for r in rows
        ]

    def exibir_um(self, item_id: int) -> Estoque | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, item, quantidade_disponivel, valor, categoria, fabricado_em_mari, ativo
                    FROM estoque
                    WHERE id = %s
                    """,
                    (item_id,),
                )
                row = cur.fetchone()

        if row is None or row[6] is not True:
            return None

        return Estoque(id=row[0], item=row[1], quantidade_disponivel=row[2], valor=row[3], categoria=row[4], fabricado_em_mari=row[5], ativo=row[6])

    def buscar_por_nome(self, termo: str) -> list[Estoque]:
        like = f"%{termo}%"
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, item, quantidade_disponivel, valor, categoria, fabricado_em_mari, ativo
                    FROM estoque
                    WHERE ativo = TRUE AND item ILIKE %s
                    ORDER BY id
                    """,
                    (like,),
                )
                rows = cur.fetchall()

        return [
            Estoque(id=r[0], item=r[1], quantidade_disponivel=r[2], valor=r[3], categoria=r[4], fabricado_em_mari=r[5], ativo=r[6])
            for r in rows
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
                    SET item = %s, quantidade_disponivel = %s, valor = %s, categoria = %s, fabricado_em_mari = %s
                    WHERE id = %s AND ativo = TRUE
                    RETURNING id, item, quantidade_disponivel, valor, categoria, fabricado_em_mari, ativo
                    """,
                    (
                        estoque.item,
                        estoque.quantidade_disponivel,
                        estoque.valor,
                        estoque.categoria,
                        estoque.fabricado_em_mari,
                        estoque.id,
                    ),
                )
                updated = cur.fetchone()
            conn.commit()

        if updated is None:
            raise ValueError("Item de estoque não encontrado ou inativo.")

        return Estoque(id=updated[0], item=updated[1], quantidade_disponivel=updated[2], valor=updated[3], categoria=updated[4], fabricado_em_mari=updated[5], ativo=updated[6])

    def buscar_por_filtros(
        self,
        nome: str | None = None,
        categoria: str | None = None,
        valor_min: Decimal | None = None,
        valor_max: Decimal | None = None,
        fabricado_em_mari: bool | None = None,
        estoque_baixo: bool = False,
    ) -> list[Estoque]:
        query = "SELECT id, item, quantidade_disponivel, valor, categoria, fabricado_em_mari, ativo FROM estoque WHERE ativo = TRUE"
        params: list = []

        if nome:
            query += " AND item ILIKE %s"
            params.append(f"%{nome}%")
        if categoria:
            query += " AND categoria = %s"
            params.append(categoria)
        if valor_min is not None:
            query += " AND valor >= %s"
            params.append(valor_min)
        if valor_max is not None:
            query += " AND valor <= %s"
            params.append(valor_max)
        if fabricado_em_mari is not None:
            query += " AND fabricado_em_mari = %s"
            params.append(fabricado_em_mari)
        if estoque_baixo:
            query += " AND quantidade_disponivel < 5"

        query += " ORDER BY id"

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

        return [
            Estoque(id=r[0], item=r[1], quantidade_disponivel=r[2], valor=r[3], categoria=r[4], fabricado_em_mari=r[5], ativo=r[6])
            for r in rows
        ]

    def remover(self, item_id: int) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE estoque SET ativo = FALSE WHERE id = %s",
                    (item_id,),
                )
            conn.commit()
