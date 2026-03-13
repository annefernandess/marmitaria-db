from dataclasses import dataclass


@dataclass
class Cliente:
    nome: str
    numero: str
    id: int | None = None
