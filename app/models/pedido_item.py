from dataclasses import dataclass


@dataclass
class PedidoItem:
    pedido_id: int
    item_id: int
    quantidade: int = 1
    id: int | None = None
