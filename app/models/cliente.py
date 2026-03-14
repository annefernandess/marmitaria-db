from dataclasses import dataclass


@dataclass
class Cliente:
    nome: str
    numero: str
    ativo: bool = True
    id: int | None = None
