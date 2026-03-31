from dataclasses import dataclass


@dataclass
class Cliente:
    nome: str
    numero: str
    torce_flamengo: bool = False
    assiste_one_piece: bool = False
    eh_de_sousa: bool = False
    ativo: bool = True
    id: int | None = None
