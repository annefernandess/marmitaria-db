from decimal import Decimal

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator

from app.database import get_connection
from app.models.cliente import Cliente
from app.models.enums import EstadoPedido, FormaPagamento, StatusPagamento
from app.models.estoque import Estoque
from app.models.pedido import Pedido
from app.models.pedido_item import PedidoItem
from app.models.usuario import Usuario
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.estoque_repository import EstoqueRepository
from app.repositories.pedido_item_repository import PedidoItemRepository
from app.repositories.pedido_repository import PedidoRepository
from app.repositories.usuario_repository import UsuarioRepository


def _decimal_to_float(value: Decimal) -> float:
    return float(value)


# --- DTOs ---


class ClienteCreate(BaseModel):
    nome: str = Field(min_length=1)
    numero: str = Field(min_length=1)
    torce_flamengo: bool = False
    assiste_one_piece: bool = False
    eh_de_sousa: bool = False


class ClienteResponse(BaseModel):
    id: int
    nome: str
    numero: str
    torce_flamengo: bool
    assiste_one_piece: bool
    eh_de_sousa: bool
    ativo: bool


class AuthRegisterRequest(BaseModel):
    nome: str = Field(min_length=1)
    email: str = Field(min_length=1)
    senha: str = Field(min_length=1)
    numero: str = Field(min_length=1)


class AuthLoginRequest(BaseModel):
    email: str = Field(min_length=1)
    senha: str = Field(min_length=1)


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str
    numero: str
    role: str
    cliente_id: int | None


class EstoqueCreate(BaseModel):
    item: str = Field(min_length=1)
    quantidade_disponivel: int = Field(ge=0)
    valor: Decimal = Field(gt=0)
    categoria: str = "Geral"
    fabricado_em_mari: bool = False


class EstoqueResponse(BaseModel):
    id: int
    item: str
    quantidade_disponivel: int
    valor: float
    categoria: str
    fabricado_em_mari: bool
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
    vendedor_id: int | None = None
    forma_pagamento: FormaPagamento | None = None
    estado: EstadoPedido = EstadoPedido.EM_ANDAMENTO
    pago: bool = False
    itens: list[PedidoItemCreate]


class PedidoUpdate(BaseModel):
    estado: EstadoPedido | None = None
    pago: bool | None = None
    status_pagamento: StatusPagamento | None = None

    @model_validator(mode="after")
    def validar_payload(self) -> "PedidoUpdate":
        if self.estado is None and self.pago is None and self.status_pagamento is None:
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
    vendedor_id: int | None
    vendedor_nome: str | None
    forma_pagamento: FormaPagamento | None
    status_pagamento: StatusPagamento
    desconto: float
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


class VendaVendedorResponse(BaseModel):
    vendedor_id: int
    vendedor_nome: str
    mes: str
    total_pedidos: int
    valor_total: float
    desconto_total: float
    pagamentos_confirmados: int


# --- Helpers ---


def _cliente_to_response(cliente: Cliente) -> ClienteResponse:
    return ClienteResponse(
        id=cliente.id,
        nome=cliente.nome,
        numero=cliente.numero,
        torce_flamengo=cliente.torce_flamengo,
        assiste_one_piece=cliente.assiste_one_piece,
        eh_de_sousa=cliente.eh_de_sousa,
        ativo=cliente.ativo,
    )


def _usuario_to_response(usuario: Usuario) -> UsuarioResponse:
    return UsuarioResponse(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        numero=usuario.numero,
        role=usuario.role,
        cliente_id=usuario.cliente_id,
    )


def _estoque_to_response(item: Estoque) -> EstoqueResponse:
    return EstoqueResponse(
        id=item.id,
        item=item.item,
        quantidade_disponivel=item.quantidade_disponivel,
        valor=_decimal_to_float(item.valor),
        categoria=item.categoria,
        fabricado_em_mari=item.fabricado_em_mari,
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


def _get_vendedor_nome(vendedor_id: int | None) -> str | None:
    if vendedor_id is None:
        return None
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT nome FROM usuarios WHERE id = %s", (vendedor_id,))
            row = cur.fetchone()
    return row[0] if row else None


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
        vendedor_id=pedido.vendedor_id,
        vendedor_nome=_get_vendedor_nome(pedido.vendedor_id),
        forma_pagamento=pedido.forma_pagamento,
        status_pagamento=pedido.status_pagamento,
        desconto=_decimal_to_float(pedido.desconto),
        itens=[_pedido_item_to_response(item) for item in itens],
    )


# --- App ---


def create_app() -> FastAPI:
    app = FastAPI(title="Marmitaria Yao API", version="0.2.0")

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

    # --- Auth ---

    @app.post("/auth/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
    def cadastrar_usuario(payload: AuthRegisterRequest) -> UsuarioResponse:
        usuario = UsuarioRepository().cadastrar(
            Usuario(
                nome=payload.nome,
                email=payload.email.lower().strip(),
                senha=payload.senha,
                numero=payload.numero,
                role="user",
            )
        )
        return _usuario_to_response(usuario)

    @app.post("/auth/login", response_model=UsuarioResponse)
    def login(payload: AuthLoginRequest) -> UsuarioResponse:
        usuario = UsuarioRepository().autenticar(
            email=payload.email.lower().strip(),
            senha=payload.senha,
        )
        return _usuario_to_response(usuario)

    # --- Clientes ---

    @app.post("/clientes", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
    def criar_cliente(payload: ClienteCreate) -> ClienteResponse:
        cliente = ClienteRepository().inserir(
            Cliente(
                nome=payload.nome,
                numero=payload.numero,
                torce_flamengo=payload.torce_flamengo,
                assiste_one_piece=payload.assiste_one_piece,
                eh_de_sousa=payload.eh_de_sousa,
            )
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
            Cliente(
                id=cliente_id,
                nome=payload.nome,
                numero=payload.numero,
                torce_flamengo=payload.torce_flamengo,
                assiste_one_piece=payload.assiste_one_piece,
                eh_de_sousa=payload.eh_de_sousa,
            )
        )
        return _cliente_to_response(cliente)

    @app.delete("/clientes/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
    def remover_cliente(cliente_id: int) -> None:
        ClienteRepository().remover(cliente_id)

    # --- Estoque ---

    @app.post("/estoque", response_model=EstoqueResponse, status_code=status.HTTP_201_CREATED)
    def criar_item_estoque(payload: EstoqueCreate) -> EstoqueResponse:
        item = EstoqueRepository().inserir(
            Estoque(
                item=payload.item,
                quantidade_disponivel=payload.quantidade_disponivel,
                valor=payload.valor,
                categoria=payload.categoria,
                fabricado_em_mari=payload.fabricado_em_mari,
            )
        )
        return _estoque_to_response(item)

    @app.get("/estoque", response_model=list[EstoqueResponse])
    def listar_estoque(
        nome: str | None = None,
        categoria: str | None = None,
        valor_min: Decimal | None = None,
        valor_max: Decimal | None = None,
        fabricado_em_mari: bool | None = None,
        estoque_baixo: bool = False,
    ) -> list[EstoqueResponse]:
        repo = EstoqueRepository()
        has_filters = any(v is not None for v in [nome, categoria, valor_min, valor_max, fabricado_em_mari]) or estoque_baixo
        if has_filters:
            itens = repo.buscar_por_filtros(
                nome=nome, categoria=categoria,
                valor_min=valor_min, valor_max=valor_max,
                fabricado_em_mari=fabricado_em_mari, estoque_baixo=estoque_baixo,
            )
        else:
            itens = repo.listar_todos()
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
                categoria=payload.categoria,
                fabricado_em_mari=payload.fabricado_em_mari,
            )
        )
        return _estoque_to_response(item)

    @app.delete("/estoque/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    def remover_item_estoque(item_id: int) -> None:
        EstoqueRepository().remover(item_id)

    # --- Pedidos ---

    @app.post("/pedidos", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
    def criar_pedido(payload: PedidoCreate) -> PedidoResponse:
        pedido = PedidoRepository().inserir(
            Pedido(
                cliente_id=payload.cliente_id,
                estado=payload.estado,
                pago=payload.pago,
                vendedor_id=payload.vendedor_id,
                forma_pagamento=payload.forma_pagamento,
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
            vendedor_id=atual.vendedor_id,
            forma_pagamento=atual.forma_pagamento,
            status_pagamento=payload.status_pagamento if payload.status_pagamento is not None else atual.status_pagamento,
            desconto=atual.desconto,
        )
        atualizado = PedidoRepository().alterar(pedido)
        return _build_pedido_response(atualizado)

    @app.delete("/pedidos/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
    def remover_pedido(pedido_id: int) -> None:
        PedidoRepository().remover(pedido_id)

    # --- Pedido Itens ---

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

    # --- Relatórios ---

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

    @app.get("/relatorios/vendas-vendedor", response_model=list[VendaVendedorResponse])
    def relatorio_vendas_vendedor() -> list[VendaVendedorResponse]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT vendedor_id, vendedor_nome, mes, total_pedidos,
                           valor_total, desconto_total, pagamentos_confirmados
                    FROM vw_vendas_por_vendedor
                    """
                )
                rows = cur.fetchall()

        return [
            VendaVendedorResponse(
                vendedor_id=r[0],
                vendedor_nome=r[1],
                mes=r[2].isoformat(),
                total_pedidos=r[3],
                valor_total=float(r[4]),
                desconto_total=float(r[5]),
                pagamentos_confirmados=r[6],
            )
            for r in rows
        ]

    return app


app = create_app()
