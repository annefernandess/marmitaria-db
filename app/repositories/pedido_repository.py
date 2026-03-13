from decimal import Decimal

from app.database import get_connection
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

    def _validar_e_calcular(self, cur, pedido: Pedido, itens: list[PedidoItem]) -> None:
        """
        Verifica disponibilidade no estoque e calcula o valor total do pedido.
        Levanta ValueError se algum item não tiver quantidade suficiente.
        """
        total = Decimal("0")

        for item in itens:
            cur.execute(
                "SELECT item, quantidade_disponivel, valor FROM estoque WHERE id = %s",
                (item.item_id,),
            )
            row = cur.fetchone()

            if row is None:
                raise ValueError(f"Item com id={item.item_id} não encontrado no estoque.")

            nome_item, qtd_disponivel, valor_unitario = row

            if qtd_disponivel < item.quantidade:
                raise ValueError(
                    f"Estoque insuficiente para '{nome_item}': "
                    f"disponível={qtd_disponivel}, solicitado={item.quantidade}."
                )

            total += Decimal(str(valor_unitario)) * item.quantidade

        pedido.valor = total
