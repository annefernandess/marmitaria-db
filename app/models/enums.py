from enum import Enum


class EstadoPedido(str, Enum):
    EM_ANDAMENTO = "EM_ANDAMENTO"
    PRONTO = "PRONTO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"


class FormaPagamento(str, Enum):
    CARTAO = "CARTAO"
    BOLETO = "BOLETO"
    PIX = "PIX"
    BERRIES = "BERRIES"


class StatusPagamento(str, Enum):
    PENDENTE = "PENDENTE"
    CONFIRMADO = "CONFIRMADO"
    REJEITADO = "REJEITADO"
