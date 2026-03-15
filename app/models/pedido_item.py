from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PedidoItem:
    pedido_id: int
    item_id: int
    quantidade: int = 1
    valor_unitario: Decimal | None = None
    id: int | None = None
