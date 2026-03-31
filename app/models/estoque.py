from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Estoque:
    item: str
    quantidade_disponivel: int
    valor: Decimal
    categoria: str = "Geral"
    fabricado_em_mari: bool = False
    ativo: bool = True
    id: int | None = None
