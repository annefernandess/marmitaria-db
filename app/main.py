from decimal import Decimal

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator

from app.models.cliente import Cliente
from app.models.enums import EstadoPedido
from app.models.estoque import Estoque
from app.models.pedido import Pedido
from app.models.pedido_item import PedidoItem
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.estoque_repository import EstoqueRepository
from app.repositories.pedido_item_repository import PedidoItemRepository
from app.repositories.pedido_repository import PedidoRepository


def _decimal_to_float(value: Decimal) -> float:
    return float(value)


class ClienteCreate(BaseModel):
    nome: str = Field(min_length=1)
    numero: str = Field(min_length=1)


class ClienteResponse(BaseModel):
    id: int
    nome: str
    numero: str
    ativo: bool


class EstoqueCreate(BaseModel):
    item: str = Field(min_length=1)
    quantidade_disponivel: int = Field(ge=0)
    valor: Decimal = Field(gt=0)


class EstoqueResponse(BaseModel):
    id: int
    item: str
    quantidade_disponivel: int
    valor: float
    ativo: bool


class PedidoItemCreate(BaseModel):
    item_id: int
    quantidade: int = Field(gt=0)


class PedidoItemUpdate(BaseModel):
    quantidade: int = Field(gt=0)


class PedidoItemResponse(BaseModel):
    id: int
    pedido_id: int
    item_id: int
    quantidade: int
    valor_unitario: float


class PedidoCreate(BaseModel):
    cliente_id: int
    estado: EstadoPedido = EstadoPedido.EM_ANDAMENTO
    pago: bool = False
    itens: list[PedidoItemCreate]


class PedidoUpdate(BaseModel):
    estado: EstadoPedido | None = None
    pago: bool | None = None

    @model_validator(mode="after")
    def validar_payload(self) -> "PedidoUpdate":
        if self.estado is None and self.pago is None:
            raise ValueError("Informe pelo menos um campo para alterar o pedido.")
        return self


class PedidoResponse(BaseModel):
    id: int
    cliente_id: int
    cliente_nome: str
    data: str
    estado: EstadoPedido
    valor: float
    pago: bool
    itens: list[PedidoItemResponse]


class RelatorioVendasResponse(BaseModel):
    total_pedidos: int
    valor_total: float
    pedidos_pagos: int
    pedidos_nao_pagos: int
    ticket_medio: float


class RelatorioEstoqueResponse(BaseModel):
    itens_cadastrados: int
    quantidade_total: int
    valor_inventario: float
    itens_sem_estoque: int


class RelatorioClientesResponse(BaseModel):
    total_clientes: int
    clientes_com_pedidos_ativos: int
    clientes_sem_pedidos: int


def _cliente_to_response(cliente: Cliente) -> ClienteResponse:
    return ClienteResponse(
        id=cliente.id,
        nome=cliente.nome,
        numero=cliente.numero,
        ativo=cliente.ativo,
    )


def _estoque_to_response(item: Estoque) -> EstoqueResponse:
    return EstoqueResponse(
        id=item.id,
        item=item.item,
        quantidade_disponivel=item.quantidade_disponivel,
        valor=_decimal_to_float(item.valor),
        ativo=item.ativo,
    )


def _pedido_item_to_response(item: PedidoItem) -> PedidoItemResponse:
    valor_unitario = item.valor_unitario or Decimal("0")
    return PedidoItemResponse(
        id=item.id,
        pedido_id=item.pedido_id,
        item_id=item.item_id,
        quantidade=item.quantidade,
        valor_unitario=_decimal_to_float(valor_unitario),
    )


def _build_pedido_response(pedido: Pedido) -> PedidoResponse:
    cliente = ClienteRepository().exibir_um(pedido.cliente_id)
    itens = [
        item
        for item in PedidoItemRepository().listar_todos()
        if item.pedido_id == pedido.id
    ]

    return PedidoResponse(
        id=pedido.id,
        cliente_id=pedido.cliente_id,
        cliente_nome=cliente.nome if cliente else "Cliente removido",
        data=pedido.data.isoformat(),
        estado=pedido.estado,
        valor=_decimal_to_float(pedido.valor),
        pago=pedido.pago,
        itens=[_pedido_item_to_response(item) for item in itens],
    )


def create_app() -> FastAPI:
    app = FastAPI(title="Marmitaria Yao API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ValueError)
    async def value_error_handler(_, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/clientes", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
    def criar_cliente(payload: ClienteCreate) -> ClienteResponse:
        cliente = ClienteRepository().inserir(
            Cliente(nome=payload.nome, numero=payload.numero)
        )
        return _cliente_to_response(cliente)

    @app.get("/clientes", response_model=list[ClienteResponse])
    def listar_clientes(nome: str | None = None) -> list[ClienteResponse]:
        repo = ClienteRepository()
        clientes = repo.buscar_por_nome(nome) if nome else repo.listar_todos()
        return [_cliente_to_response(cliente) for cliente in clientes]

    @app.get("/clientes/{cliente_id}", response_model=ClienteResponse)
    def exibir_cliente(cliente_id: int) -> ClienteResponse:
        cliente = ClienteRepository().exibir_um(cliente_id)
        if cliente is None:
            raise HTTPException(status_code=404, detail="Cliente não encontrado.")
        return _cliente_to_response(cliente)

    @app.put("/clientes/{cliente_id}", response_model=ClienteResponse)
    def alterar_cliente(cliente_id: int, payload: ClienteCreate) -> ClienteResponse:
        cliente = ClienteRepository().alterar(
            Cliente(id=cliente_id, nome=payload.nome, numero=payload.numero)
        )
        return _cliente_to_response(cliente)

    @app.delete("/clientes/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
    def remover_cliente(cliente_id: int) -> None:
        ClienteRepository().remover(cliente_id)

    @app.post("/estoque", response_model=EstoqueResponse, status_code=status.HTTP_201_CREATED)
    def criar_item_estoque(payload: EstoqueCreate) -> EstoqueResponse:
        item = EstoqueRepository().inserir(
            Estoque(
                item=payload.item,
                quantidade_disponivel=payload.quantidade_disponivel,
                valor=payload.valor,
            )
        )
        return _estoque_to_response(item)

    @app.get("/estoque", response_model=list[EstoqueResponse])
    def listar_estoque(nome: str | None = None) -> list[EstoqueResponse]:
        repo = EstoqueRepository()
        itens = repo.buscar_por_nome(nome) if nome else repo.listar_todos()
        return [_estoque_to_response(item) for item in itens]

    @app.get("/estoque/{item_id}", response_model=EstoqueResponse)
    def exibir_item_estoque(item_id: int) -> EstoqueResponse:
        item = EstoqueRepository().exibir_um(item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Item de estoque não encontrado.")
        return _estoque_to_response(item)

    @app.put("/estoque/{item_id}", response_model=EstoqueResponse)
    def alterar_item_estoque(item_id: int, payload: EstoqueCreate) -> EstoqueResponse:
        item = EstoqueRepository().alterar(
            Estoque(
                id=item_id,
                item=payload.item,
                quantidade_disponivel=payload.quantidade_disponivel,
                valor=payload.valor,
            )
        )
        return _estoque_to_response(item)

    @app.delete("/estoque/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    def remover_item_estoque(item_id: int) -> None:
        EstoqueRepository().remover(item_id)

    @app.post("/pedidos", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
    def criar_pedido(payload: PedidoCreate) -> PedidoResponse:
        pedido = PedidoRepository().inserir(
            Pedido(
                cliente_id=payload.cliente_id,
                estado=payload.estado,
                pago=payload.pago,
            ),
            [
                PedidoItem(pedido_id=0, item_id=item.item_id, quantidade=item.quantidade)
                for item in payload.itens
            ],
        )
        return _build_pedido_response(pedido)

    @app.get("/pedidos", response_model=list[PedidoResponse])
    def listar_pedidos(
        estado: EstadoPedido | None = None,
        cliente_nome: str | None = None,
    ) -> list[PedidoResponse]:
        pedidos = PedidoRepository().listar_todos()
        responses = [_build_pedido_response(pedido) for pedido in pedidos]

        if estado is not None:
            responses = [pedido for pedido in responses if pedido.estado == estado]

        if cliente_nome:
            termo = cliente_nome.lower()
            responses = [
                pedido
                for pedido in responses
                if termo in pedido.cliente_nome.lower()
            ]

        return responses

    @app.get("/pedidos/{pedido_id}", response_model=PedidoResponse)
    def exibir_pedido(pedido_id: int) -> PedidoResponse:
        pedido = PedidoRepository().exibir_um(pedido_id)
        if pedido is None:
            raise HTTPException(status_code=404, detail="Pedido não encontrado.")
        return _build_pedido_response(pedido)

    @app.patch("/pedidos/{pedido_id}", response_model=PedidoResponse)
    def alterar_pedido(pedido_id: int, payload: PedidoUpdate) -> PedidoResponse:
        atual = PedidoRepository().exibir_um(pedido_id)
        if atual is None:
            raise HTTPException(status_code=404, detail="Pedido não encontrado.")

        pedido = Pedido(
            id=atual.id,
            cliente_id=atual.cliente_id,
            data=atual.data,
            estado=payload.estado if payload.estado is not None else atual.estado,
            valor=atual.valor,
            pago=payload.pago if payload.pago is not None else atual.pago,
        )
        atualizado = PedidoRepository().alterar(pedido)
        return _build_pedido_response(atualizado)

    @app.delete("/pedidos/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
    def remover_pedido(pedido_id: int) -> None:
        PedidoRepository().remover(pedido_id)

    @app.get("/pedido-itens", response_model=list[PedidoItemResponse])
    def listar_itens_pedido(pedido_id: int | None = None) -> list[PedidoItemResponse]:
        itens = PedidoItemRepository().listar_todos()
        if pedido_id is not None:
            itens = [item for item in itens if item.pedido_id == pedido_id]
        return [_pedido_item_to_response(item) for item in itens]

    @app.get("/pedido-itens/{pedido_item_id}", response_model=PedidoItemResponse)
    def exibir_item_pedido(pedido_item_id: int) -> PedidoItemResponse:
        item = PedidoItemRepository().exibir_um(pedido_item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Item de pedido não encontrado.")
        return _pedido_item_to_response(item)

    @app.patch("/pedido-itens/{pedido_item_id}", response_model=PedidoItemResponse)
    def alterar_item_pedido(
        pedido_item_id: int,
        payload: PedidoItemUpdate,
    ) -> PedidoItemResponse:
        atual = PedidoItemRepository().exibir_um(pedido_item_id)
        if atual is None:
            raise HTTPException(status_code=404, detail="Item de pedido não encontrado.")

        atualizado = PedidoItemRepository().alterar(
            PedidoItem(
                id=atual.id,
                pedido_id=atual.pedido_id,
                item_id=atual.item_id,
                quantidade=payload.quantidade,
            )
        )
        return _pedido_item_to_response(atualizado)

    @app.delete("/pedido-itens/{pedido_item_id}", status_code=status.HTTP_204_NO_CONTENT)
    def remover_item_pedido(pedido_item_id: int) -> None:
        PedidoItemRepository().remover(pedido_item_id)

    @app.get("/relatorios/vendas", response_model=RelatorioVendasResponse)
    def relatorio_vendas() -> RelatorioVendasResponse:
        pedidos = PedidoRepository().listar_todos()
        total_pedidos = len(pedidos)
        valor_total = sum((pedido.valor for pedido in pedidos), Decimal("0"))
        pedidos_pagos = sum(1 for pedido in pedidos if pedido.pago)
        pedidos_nao_pagos = total_pedidos - pedidos_pagos
        ticket_medio = (valor_total / total_pedidos) if total_pedidos else Decimal("0")

        return RelatorioVendasResponse(
            total_pedidos=total_pedidos,
            valor_total=_decimal_to_float(valor_total),
            pedidos_pagos=pedidos_pagos,
            pedidos_nao_pagos=pedidos_nao_pagos,
            ticket_medio=_decimal_to_float(ticket_medio),
        )

    @app.get("/relatorios/estoque", response_model=RelatorioEstoqueResponse)
    def relatorio_estoque() -> RelatorioEstoqueResponse:
        itens = EstoqueRepository().listar_todos()
        quantidade_total = sum(item.quantidade_disponivel for item in itens)
        valor_inventario = sum(
            (item.valor * item.quantidade_disponivel for item in itens),
            Decimal("0"),
        )
        itens_sem_estoque = sum(1 for item in itens if item.quantidade_disponivel == 0)

        return RelatorioEstoqueResponse(
            itens_cadastrados=len(itens),
            quantidade_total=quantidade_total,
            valor_inventario=_decimal_to_float(valor_inventario),
            itens_sem_estoque=itens_sem_estoque,
        )

    @app.get("/relatorios/clientes", response_model=RelatorioClientesResponse)
    def relatorio_clientes() -> RelatorioClientesResponse:
        clientes = ClienteRepository().listar_todos()
        pedidos = PedidoRepository().listar_todos()

        clientes_com_pedidos_ativos_ids = {
            pedido.cliente_id
            for pedido in pedidos
            if pedido.estado in {EstadoPedido.EM_ANDAMENTO, EstadoPedido.PRONTO}
        }
        clientes_ids = {cliente.id for cliente in clientes}
        clientes_sem_pedidos = clientes_ids - {pedido.cliente_id for pedido in pedidos}

        return RelatorioClientesResponse(
            total_clientes=len(clientes),
            clientes_com_pedidos_ativos=len(clientes_com_pedidos_ativos_ids),
            clientes_sem_pedidos=len(clientes_sem_pedidos),
        )

    return app


app = create_app()
