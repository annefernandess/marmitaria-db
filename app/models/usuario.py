from dataclasses import dataclass


@dataclass
class Usuario:
    nome: str
    email: str
    senha: str
    numero: str
    role: str = "user"
    cliente_id: int | None = None
    ativo: bool = True
    id: int | None = None
