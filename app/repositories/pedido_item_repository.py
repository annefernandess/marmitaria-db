from decimal import Decimal

from app.database import get_connection
from app.models.enums import EstadoPedido
from app.models.pedido_item import PedidoItem


class PedidoItemRepository:
    def listar_todos(self) -> list[PedidoItem]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, pedido_id, item_id, quantidade, valor_unitario
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
                valor_unitario=row[4],
            )
            for row in rows
        ]

    def exibir_um(self, pedido_item_id: int) -> PedidoItem | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, pedido_id, item_id, quantidade, valor_unitario
                    FROM pedido_itens
                    WHERE id = %s
                    """,
                    (pedido_item_id,),
                )
                row = cur.fetchone()

        if row is None:
            return None

        return PedidoItem(
            id=row[0],
            pedido_id=row[1],
            item_id=row[2],
            quantidade=row[3],
            valor_unitario=row[4],
        )

    def alterar(self, pedido_item: PedidoItem) -> PedidoItem:
        if pedido_item.id is None:
            raise ValueError("ID do item do pedido é obrigatório para alterar.")

        if pedido_item.quantidade <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")

        with get_connection() as conn:
            with conn.cursor() as cur:
                # Busca dados atuais sem lock
                cur.execute(
                    """
                    SELECT pedido_id, item_id, quantidade, valor_unitario
                    FROM pedido_itens
                    WHERE id = %s
                    """,
                    (pedido_item.id,),
                )
                atual = cur.fetchone()

                if atual is None:
                    raise ValueError("Item de pedido não encontrado.")

                pedido_id_atual, item_id_atual, qtd_atual, valor_unitario = atual
                delta = pedido_item.quantidade - qtd_atual

                # Se aumentar a quantidade, trava estoque antes para evitar deadlock
                if delta > 0:
                    cur.execute(
                        "SELECT quantidade_disponivel, ativo FROM estoque WHERE id = %s FOR UPDATE",
                        (pedido_item.item_id,),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise ValueError("Item do estoque não encontrado.")

                    disponivel, ativo = row
                    if not ativo:
                        raise ValueError("Item do estoque está inativo.")

                    if disponivel < delta:
                        raise ValueError("Estoque insuficiente para aumentar a quantidade do item.")

                # Trava pedido_itens e pedidos (ordem: estoque -> pedido_itens -> pedidos)
                cur.execute(
                    """
                    SELECT pedido_id, item_id, quantidade, valor_unitario
                    FROM pedido_itens
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (pedido_item.id,),
                )
                atual = cur.fetchone()
                if atual is None:
                    raise ValueError("Item de pedido não encontrado (após lock).")

                pedido_id_atual, item_id_atual, qtd_atual, valor_unitario = atual

                cur.execute(
                    """
                    SELECT p.estado, c.ativo
                    FROM pedidos p
                    JOIN clientes c ON c.id = p.cliente_id
                    WHERE p.id = %s
                    FOR UPDATE
                    """,
                    (pedido_id_atual,),
                )
                pedido_info = cur.fetchone()

                if pedido_info is None:
                    raise ValueError("Pedido não encontrado para o item.")

                estado_pedido = EstadoPedido(pedido_info[0])
                cliente_ativo = pedido_info[1]

                if estado_pedido in {EstadoPedido.PRONTO, EstadoPedido.ENTREGUE, EstadoPedido.CANCELADO}:
                    raise ValueError("Não é permitido alterar itens em estado do pedido já finalizado.")

                if not cliente_ativo:
                    raise ValueError("Não é permitido alterar itens de cliente inativo.")

                if pedido_item.item_id != item_id_atual:
                    raise ValueError("Alteração de item_id não é suportada.")

                if delta > 0:
                    cur.execute(
                        """
                        UPDATE estoque
                        SET quantidade_disponivel = quantidade_disponivel - %s
                        WHERE id = %s
                        """,
                        (delta, pedido_item.item_id),
                    )
                elif delta < 0:
                    cur.execute(
                        """
                        UPDATE estoque
                        SET quantidade_disponivel = quantidade_disponivel + %s
                        WHERE id = %s
                        """,
                        (-delta, pedido_item.item_id),
                    )

                cur.execute(
                    """
                    UPDATE pedido_itens
                    SET quantidade = %s
                    WHERE id = %s
                    RETURNING id, pedido_id, item_id, quantidade, valor_unitario
                    """,
                    (pedido_item.quantidade, pedido_item.id),
                )
                updated = cur.fetchone()

                cur.execute(
                    """
                    SELECT COALESCE(SUM(pi.quantidade * pi.valor_unitario), 0)
                    FROM pedido_itens pi
                    WHERE pi.pedido_id = %s
                    """,
                    (pedido_id_atual,),
                )
                total = cur.fetchone()[0] or Decimal("0")

                cur.execute(
                    "UPDATE pedidos SET valor = %s WHERE id = %s",
                    (total, pedido_id_atual),
                )
            conn.commit()

        return PedidoItem(
            id=updated[0],
            pedido_id=updated[1],
            item_id=updated[2],
            quantidade=updated[3],
            valor_unitario=updated[4],
        )

    def remover(self, pedido_item_id: int) -> None:
        """Remove um item de pedido e restaura o estoque correspondente.

        Usa ``DELETE ... RETURNING`` para garantir que apenas a transação que
        de fato removeu o registro devolva a quantidade ao estoque. Em cenários
        concorrentes, uma segunda chamada para o mesmo ``pedido_item_id`` não
        encontrará linhas para apagar e, consequentemente, não restaurará nada.
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM pedido_itens
                    WHERE id = %s
                    RETURNING item_id, quantidade
                    """,
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

            conn.commit()
