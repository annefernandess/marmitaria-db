from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from app.models.enums import EstadoPedido, FormaPagamento, StatusPagamento


@dataclass
class Pedido:
    cliente_id: int
    data: date = field(default_factory=date.today)
    estado: EstadoPedido = EstadoPedido.EM_ANDAMENTO
    valor: Decimal = field(default_factory=lambda: Decimal("0"))
    pago: bool = False
    vendedor_id: int | None = None
    forma_pagamento: FormaPagamento | None = None
    status_pagamento: StatusPagamento = StatusPagamento.PENDENTE
    desconto: Decimal = field(default_factory=lambda: Decimal("0"))
    id: int | None = None
