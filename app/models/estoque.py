from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Estoque:
    item: str
    quantidade_disponivel: int
    valor: Decimal
    id: int | None = None
