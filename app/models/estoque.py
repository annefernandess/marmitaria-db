from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Estoque:
    item: str
    quantidade_disponivel: int
    valor: Decimal
    ativo: bool = True
    id: int | None = None
