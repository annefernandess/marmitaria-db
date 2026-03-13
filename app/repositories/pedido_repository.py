from decimal import Decimal

from app.database import get_connection
from app.models.enums import EstadoPedido
from app.models.pedido import Pedido
from app.models.pedido_item import PedidoItem


class PedidoRepository:
    def inserir(self, pedido: Pedido, itens: list[PedidoItem]) -> Pedido:
        """
        Insere um pedido e seus itens dentro de uma única transação.

        Valida o estoque disponível para cada item antes de qualquer alteração.
        Calcula o valor total do pedido a partir dos preços atuais do estoque.
        Decrementa o estoque de cada item ao confirmar o pedido.
        """
        if not itens:
            raise ValueError("O pedido deve ter pelo menos um item.")

        itens = self._mesclar_itens(itens)

        with get_connection() as conn:
            with conn.cursor() as cur:
                self._validar_e_calcular(cur, pedido, itens)

                cur.execute(
                    """
                    INSERT INTO pedidos (cliente_id, data, estado, valor, pago)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        pedido.cliente_id,
                        pedido.data,
                        pedido.estado.value,
                        pedido.valor,
                        pedido.pago,
                    ),
                )
                pedido.id = cur.fetchone()[0]

                for item in itens:
                    item.pedido_id = pedido.id
                    cur.execute(
                        """
                        INSERT INTO pedido_itens (pedido_id, item_id, quantidade)
                        VALUES (%s, %s, %s)
                        RETURNING id
                        """,
                        (item.pedido_id, item.item_id, item.quantidade),
                    )
                    item.id = cur.fetchone()[0]

                    cur.execute(
                        """
                        UPDATE estoque
                        SET quantidade_disponivel = quantidade_disponivel - %s
                        WHERE id = %s
                        """,
                        (item.quantidade, item.item_id),
                    )

            conn.commit()
        return pedido

    def listar_todos(self) -> list[Pedido]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, cliente_id, data, estado, valor, pago
                    FROM pedidos
                    ORDER BY id
                    """
                )
                rows = cur.fetchall()

        return [
            Pedido(
                id=row[0],
                cliente_id=row[1],
                data=row[2],
                estado=EstadoPedido(row[3]),
                valor=row[4],
                pago=row[5],
            )
            for row in rows
        ]

    def remover(self, pedido_id: int) -> None:
        """Remove um pedido e restaura o estoque a partir dos itens do pedido."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT item_id, quantidade FROM pedido_itens WHERE pedido_id = %s",
                    (pedido_id,),
                )
                itens = cur.fetchall()

                for item_id, quantidade in itens:
                    cur.execute(
                        """
                        UPDATE estoque
                        SET quantidade_disponivel = quantidade_disponivel + %s
                        WHERE id = %s
                        """,
                        (quantidade, item_id),
                    )

                cur.execute("DELETE FROM pedidos WHERE id = %s", (pedido_id,))

            conn.commit()

    def _mesclar_itens(self, itens: list[PedidoItem]) -> list[PedidoItem]:
        """
        Une linhas com o mesmo item_id somando as quantidades.

        Muta a quantidade do primeiro objeto encontrado para cada item_id,
        preservando as referências originais (quem chamou continua apontando
        para os mesmos objetos e verá pedido_id/id preenchidos após o insert).
        """
        seen: dict[int, PedidoItem] = {}
        result: list[PedidoItem] = []
        for item in itens:
            if item.item_id in seen:
                seen[item.item_id].quantidade += item.quantidade
            else:
                seen[item.item_id] = item
                result.append(item)
        return result

    def _validar_e_calcular(self, cur, pedido: Pedido, itens: list[PedidoItem]) -> None:
        """
        Verifica disponibilidade no estoque e calcula o valor total do pedido.

        Agrupa quantidades por item_id antes de validar, evitando que linhas
        repetidas do mesmo item passem individualmente mas excedam o estoque
        no total. Usa FOR UPDATE para travar as linhas do estoque durante a
        transação e prevenir race conditions em pedidos simultâneos.
        """
        # Soma todas as quantidades do mesmo item antes de qualquer validação
        qtd_por_item: dict[int, int] = {}
        for item in itens:
            qtd_por_item[item.item_id] = qtd_por_item.get(item.item_id, 0) + item.quantidade

        total = Decimal("0")

        for item_id, qtd_total in qtd_por_item.items():
            cur.execute(
                "SELECT item, quantidade_disponivel, valor FROM estoque WHERE id = %s FOR UPDATE",
                (item_id,),
            )
            row = cur.fetchone()

            if row is None:
                raise ValueError(f"Item com id={item_id} não encontrado no estoque.")

            nome_item, qtd_disponivel, valor_unitario = row

            if qtd_disponivel < qtd_total:
                raise ValueError(
                    f"Estoque insuficiente para '{nome_item}': "
                    f"disponível={qtd_disponivel}, solicitado={qtd_total}."
                )

            total += Decimal(str(valor_unitario)) * qtd_total

        pedido.valor = total
