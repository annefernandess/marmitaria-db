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
                self._validar_cliente(cur, pedido.cliente_id)
                valor_por_item = self._validar_e_calcular(cur, pedido, itens)

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
                    item.valor_unitario = valor_por_item[item.item_id]
                    cur.execute(
                        """
                        INSERT INTO pedido_itens (pedido_id, item_id, quantidade, valor_unitario)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                        """,
                        (item.pedido_id, item.item_id, item.quantidade, item.valor_unitario),
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
        """Remove um pedido e restaura o estoque a partir dos itens removidos."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Remove primeiro os itens do pedido, recuperando exatamente
                # o que foi apagado para restaurar o estoque na sequência.
                cur.execute(
                    """
                    DELETE FROM pedido_itens
                    WHERE pedido_id = %s
                    RETURNING item_id, quantidade
                    """,
                    (pedido_id,),
                )
                itens_removidos = cur.fetchall()

                for item_id, quantidade in itens_removidos:
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

    def exibir_um(self, pedido_id: int) -> Pedido | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, cliente_id, data, estado, valor, pago
                    FROM pedidos
                    WHERE id = %s
                    """,
                    (pedido_id,),
                )
                row = cur.fetchone()

        if row is None:
            return None

        return Pedido(
            id=row[0],
            cliente_id=row[1],
            data=row[2],
            estado=EstadoPedido(row[3]),
            valor=row[4],
            pago=row[5],
        )

    def alterar(self, pedido: Pedido) -> Pedido:
        if pedido.id is None:
            raise ValueError("ID do pedido é obrigatório para alterar.")

        ordem_estado = [EstadoPedido.EM_ANDAMENTO, EstadoPedido.PRONTO, EstadoPedido.ENTREGUE, EstadoPedido.CANCELADO]
        transicoes_permitidas = {
            EstadoPedido.EM_ANDAMENTO: {EstadoPedido.PRONTO, EstadoPedido.CANCELADO},
            EstadoPedido.PRONTO: {EstadoPedido.ENTREGUE, EstadoPedido.CANCELADO},
        }

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT estado, pago, cliente_id FROM pedidos WHERE id = %s FOR UPDATE",
                    (pedido.id,),
                )
                row = cur.fetchone()

                if row is None:
                    raise ValueError("Pedido não encontrado.")

                estado_atual = EstadoPedido(row[0])
                pago_atual = row[1]
                cliente_id = row[2]

                cur.execute(
                    "SELECT ativo FROM clientes WHERE id = %s FOR UPDATE",
                    (cliente_id,),
                )
                cliente_row = cur.fetchone()
                if cliente_row is None or cliente_row[0] is not True:
                    raise ValueError("Pedido de cliente inativo não pode ser alterado.")

                if estado_atual == EstadoPedido.CANCELADO:
                    raise ValueError("Pedido cancelado não pode ser alterado.")

                if estado_atual == EstadoPedido.ENTREGUE:
                    raise ValueError("Pedido entregue não pode ser alterado.")

                if pago_atual is True and pedido.pago is False:
                    raise ValueError("Não é permitido retroceder pagamento.")

                if ordem_estado.index(pedido.estado) < ordem_estado.index(estado_atual):
                    raise ValueError("Não é permitido retroceder estado.")

                if pedido.estado != estado_atual:
                    permitidos = transicoes_permitidas.get(estado_atual, set())
                    if pedido.estado not in permitidos:
                        raise ValueError("Transição de estado não permitida.")

                if pedido.estado == EstadoPedido.CANCELADO and pedido.pago:
                    raise ValueError("Pedido cancelado não pode ser marcado como pago.")

                cur.execute(
                    """
                    UPDATE pedidos
                    SET estado = %s, pago = %s
                    WHERE id = %s
                    RETURNING id, estado, pago
                    """,
                    (pedido.estado.value, pedido.pago, pedido.id),
                )
                updated = cur.fetchone()

                # Utiliza DELETE ... RETURNING para evitar restaurar o estoque em dobro
                # caso o mesmo pedido seja posteriormente removido
                # (remover() também deleta itens e restaura estoque).
                if pedido.estado == EstadoPedido.CANCELADO:
                    cur.execute(
                        """
                        DELETE FROM pedido_itens
                        WHERE pedido_id = %s
                        RETURNING item_id, quantidade
                        """,
                        (pedido.id,),
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

                    # Após remover todos os itens do pedido, o valor total deve ser zerado
                    cur.execute(
                        """
                        UPDATE pedidos
                        SET valor = 0
                        WHERE id = %s
                        """,
                        (pedido.id,),
                    )
            conn.commit()

        pedido.estado = EstadoPedido(updated[1])
        pedido.pago = updated[2]
        return pedido

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

    def _validar_e_calcular(self, cur, pedido: Pedido, itens: list[PedidoItem]) -> dict[int, Decimal]:
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
        valor_por_item: dict[int, Decimal] = {}

        for item_id, qtd_total in qtd_por_item.items():
            cur.execute(
                "SELECT item, quantidade_disponivel, valor, ativo FROM estoque WHERE id = %s FOR UPDATE",
                (item_id,),
            )
            row = cur.fetchone()

            if row is None:
                raise ValueError(f"Item com id={item_id} não encontrado no estoque.")

            nome_item, qtd_disponivel, valor_unitario, ativo = row

            if not ativo:
                raise ValueError(f"Item '{nome_item}' está inativo e não pode ser usado em pedidos.")

            if qtd_disponivel < qtd_total:
                raise ValueError(
                    f"Estoque insuficiente para '{nome_item}': "
                    f"disponível={qtd_disponivel}, solicitado={qtd_total}."
                )

            valor = Decimal(str(valor_unitario))
            valor_por_item[item_id] = valor
            total += valor * qtd_total

        pedido.valor = total
        return valor_por_item

    def _validar_cliente(self, cur, cliente_id: int) -> None:
        cur.execute(
            "SELECT ativo FROM clientes WHERE id = %s FOR UPDATE",
            (cliente_id,),
        )
        row = cur.fetchone()

        if row is None:
            raise ValueError(f"Cliente com id={cliente_id} não encontrado.")

        ativo = row[0]
        if not ativo:
            raise ValueError("Cliente inativo não pode fazer pedidos.")
