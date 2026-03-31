# Parte 2 — Sistema de Vendas Completo

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Estender o sistema Marmitaria Yao com módulo de vendas completo: vendedor, forma de pagamento com status de confirmação, desconto por perfil do cliente (Flamengo/One Piece/Sousa), filtros avançados de estoque (categoria, faixa de preço, fabricado em Mari, estoque baixo), relatório mensal de vendas por vendedor, VIEW e STORED PROCEDURE no banco.

**Architecture:** Evolução incremental do schema existente (`db/init.sql`) com `ADD COLUMN IF NOT EXISTS` + novos ENUMs. Backend mantém a mesma arquitetura (models → repositories → main.py). Lógica de desconto vive em uma FUNCTION PostgreSQL chamada pelo repository. VIEW materializa o relatório mensal por vendedor. Frontend estende as telas existentes para os novos campos.

**Tech Stack:** Python 3.12, FastAPI, psycopg2, PostgreSQL 16, Next.js 16, React 19, TypeScript, Tailwind v4

---

## Status Atual vs Requisitos da Parte 2

| Requisito | Status | O que falta |
|---|---|---|
| Cliente faz várias compras com 1+ itens | ✅ Pronto | — |
| Navegar sem login, compra exige dados | ✅ Pronto | — |
| Cliente consulta dados e pedidos | ✅ Pronto | — |
| Vendedor efetiva a compra | ❌ | `vendedor_id` em pedidos, role vendedor |
| Forma de pagamento + status confirmação | ❌ | ENUMs + colunas em pedidos |
| Desconto Flamengo/One Piece/Sousa | ❌ | Campos em clientes + lógica |
| Sem compra se sem estoque | ✅ Pronto | — |
| Busca por nome, faixa preço, categoria, Mari | ⚠️ Parcial | `categoria`, `fabricado_em_mari` em estoque + filtros |
| Filtro < 5 unidades (funcionário) | ❌ | Filtro no endpoint |
| Relatório mensal vendas por vendedor | ❌ | VIEW + endpoint |
| VIEW no banco | ❌ | Criar VIEW |
| STORED PROCEDURE no banco | ❌ | Criar FUNCTION |
| Índices e integridade referencial | ✅ Pronto | Novos índices para colunas novas |
| Interface gráfica | ✅ Pronto | Atualizar telas com novos campos |

---

## Task 1: Evolução do Schema — Novos ENUMs e Colunas

**Files:**
- Modify: `db/init.sql`

**Step 1: Adicionar novos ENUMs e colunas ao init.sql**

Adicionar ao final do arquivo (antes dos índices):

```sql
-- ============================================================
--  Parte 2 — Módulo de Vendas
-- ============================================================

-- Novos ENUMs
DO $$ BEGIN
    CREATE TYPE forma_pagamento AS ENUM ('CARTAO', 'BOLETO', 'PIX', 'BERRIES');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE status_pagamento AS ENUM ('PENDENTE', 'CONFIRMADO', 'REJEITADO');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Novas colunas em clientes (perfil para desconto)
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS torce_flamengo BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS assiste_one_piece BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS eh_de_sousa BOOLEAN NOT NULL DEFAULT FALSE;

-- Novas colunas em estoque (categoria e origem)
ALTER TABLE estoque ADD COLUMN IF NOT EXISTS categoria VARCHAR(100) NOT NULL DEFAULT 'Geral';
ALTER TABLE estoque ADD COLUMN IF NOT EXISTS fabricado_em_mari BOOLEAN NOT NULL DEFAULT FALSE;

-- Novas colunas em pedidos (vendedor, pagamento, desconto)
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS vendedor_id INT NULL REFERENCES usuarios(id);
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS forma_pagamento forma_pagamento NULL;
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS status_pagamento status_pagamento NOT NULL DEFAULT 'PENDENTE';
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS desconto NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (desconto >= 0);

-- Novos índices
CREATE INDEX IF NOT EXISTS idx_pedidos_vendedor ON pedidos(vendedor_id);
CREATE INDEX IF NOT EXISTS idx_estoque_categoria ON estoque(categoria);
CREATE INDEX IF NOT EXISTS idx_pedidos_data ON pedidos(data);
```

**Step 2: Adicionar STORED FUNCTION para cálculo de desconto**

```sql
-- STORED FUNCTION: calcula o percentual de desconto de um cliente
CREATE OR REPLACE FUNCTION calcular_desconto(p_cliente_id INT)
RETURNS NUMERIC AS $$
DECLARE
    desconto NUMERIC := 0;
    v_torce_flamengo BOOLEAN;
    v_assiste_one_piece BOOLEAN;
    v_eh_de_sousa BOOLEAN;
BEGIN
    SELECT torce_flamengo, assiste_one_piece, eh_de_sousa
    INTO v_torce_flamengo, v_assiste_one_piece, v_eh_de_sousa
    FROM clientes
    WHERE id = p_cliente_id AND ativo = TRUE;

    IF NOT FOUND THEN
        RETURN 0;
    END IF;

    IF v_torce_flamengo THEN desconto := desconto + 5; END IF;
    IF v_assiste_one_piece THEN desconto := desconto + 5; END IF;
    IF v_eh_de_sousa THEN desconto := desconto + 5; END IF;

    RETURN desconto;
END;
$$ LANGUAGE plpgsql;
```

**Step 3: Adicionar VIEW de vendas por vendedor**

```sql
-- VIEW: relatório mensal de vendas por vendedor
CREATE OR REPLACE VIEW vw_vendas_por_vendedor AS
SELECT
    u.id AS vendedor_id,
    u.nome AS vendedor_nome,
    DATE_TRUNC('month', p.data)::DATE AS mes,
    COUNT(*) AS total_pedidos,
    SUM(p.valor) AS valor_total,
    SUM(p.desconto) AS desconto_total,
    SUM(CASE WHEN p.status_pagamento = 'CONFIRMADO' THEN 1 ELSE 0 END) AS pagamentos_confirmados
FROM pedidos p
JOIN usuarios u ON u.id = p.vendedor_id
GROUP BY u.id, u.nome, DATE_TRUNC('month', p.data)
ORDER BY mes DESC, valor_total DESC;
```

**Step 4: Atualizar seed data para novos campos**

```sql
-- Atualizar categorias dos itens de estoque existentes
UPDATE estoque SET categoria = 'Salgados' WHERE item ILIKE '%coxinha%' OR item ILIKE '%empada%' OR item ILIKE '%pastel%' OR item ILIKE '%kibe%' OR item ILIKE '%enroladinho%';
UPDATE estoque SET categoria = 'Bebidas' WHERE item ILIKE '%suco%' OR item ILIKE '%refrigerante%';

-- Atualizar perfis dos clientes demo
UPDATE clientes SET torce_flamengo = TRUE WHERE nome = 'Maria Silva';
UPDATE clientes SET assiste_one_piece = TRUE WHERE nome = 'João Souza';
UPDATE clientes SET eh_de_sousa = TRUE, torce_flamengo = TRUE WHERE nome = 'Ana Costa';
```

**Step 5: Verificar que o schema é válido**

Run: `docker compose -f .devcontainer/docker-compose.yml down -v && docker compose -f .devcontainer/docker-compose.yml up db -d`
(ou dentro do container: re-executar o init.sql)

**Step 6: Commit**

```bash
git add db/init.sql
git commit -m "feat: schema parte 2 — vendedor, pagamento, desconto, categoria, VIEW e FUNCTION"
```

---

## Task 2: Atualizar Modelos Python (ENUMs + Dataclasses)

**Files:**
- Modify: `app/models/enums.py`
- Modify: `app/models/cliente.py`
- Modify: `app/models/estoque.py`
- Modify: `app/models/pedido.py`

**Step 1: Adicionar novos ENUMs**

Em `app/models/enums.py`:

```python
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
```

**Step 2: Atualizar Cliente**

Em `app/models/cliente.py`:

```python
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
```

**Step 3: Atualizar Estoque**

Em `app/models/estoque.py`:

```python
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
```

**Step 4: Atualizar Pedido**

Em `app/models/pedido.py`:

```python
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from app.models.enums import EstadoPedido, FormaPagamento, StatusPagamento


@dataclass
class Pedido:
    cliente_id: int
    data: date = field(default_factory=date.today)
    estado: EstadoPedido = EstadoPedido.EM_ANDAMENTO
    valor: Decimal = field(default_factory=lambda: Decimal("0"))
    pago: bool = False
    vendedor_id: int | None = None
    forma_pagamento: FormaPagamento | None = None
    status_pagamento: StatusPagamento = StatusPagamento.PENDENTE
    desconto: Decimal = field(default_factory=lambda: Decimal("0"))
    id: int | None = None
```

**Step 5: Commit**

```bash
git add app/models/
git commit -m "feat: modelos parte 2 — novos enums, campos de desconto, categoria e pagamento"
```

---

## Task 3: Atualizar ClienteRepository (TDD)

**Files:**
- Modify: `app/repositories/cliente_repository.py`
- Modify: `tests/test_cliente_repository.py`

**Step 1: Escrever testes para novos campos do cliente**

Adicionar em `tests/test_cliente_repository.py`:

```python
def test_inserir_cliente_com_perfil_desconto(db):
    repo = ClienteRepository()
    cliente = repo.inserir(
        Cliente(nome="Luffy Fan", numero="999", torce_flamengo=True, assiste_one_piece=True, eh_de_sousa=False)
    )
    assert cliente.id is not None
    recuperado = repo.exibir_um(cliente.id)
    assert recuperado.torce_flamengo is True
    assert recuperado.assiste_one_piece is True
    assert recuperado.eh_de_sousa is False


def test_alterar_cliente_perfil_desconto(db):
    repo = ClienteRepository()
    cliente = repo.inserir(Cliente(nome="Teste Perfil", numero="888"))
    assert cliente.torce_flamengo is False

    cliente.torce_flamengo = True
    cliente.eh_de_sousa = True
    atualizado = repo.alterar(cliente)
    assert atualizado.torce_flamengo is True
    assert atualizado.eh_de_sousa is True
```

**Step 2: Rodar testes para confirmar falha**

Run: `uv run pytest tests/test_cliente_repository.py::test_inserir_cliente_com_perfil_desconto tests/test_cliente_repository.py::test_alterar_cliente_perfil_desconto -v`
Expected: FAIL (campos não são lidos/escritos no repository)

**Step 3: Atualizar ClienteRepository para os novos campos**

Em `inserir`: adicionar `torce_flamengo`, `assiste_one_piece`, `eh_de_sousa` no INSERT.
Em `listar_todos`, `exibir_um`, `buscar_por_nome`: adicionar os novos campos no SELECT e no construtor do `Cliente`.
Em `alterar`: adicionar os novos campos no UPDATE.

Exemplo para `inserir`:
```python
cur.execute(
    """
    INSERT INTO clientes (nome, numero, torce_flamengo, assiste_one_piece, eh_de_sousa, ativo)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id
    """,
    (cliente.nome, cliente.numero, cliente.torce_flamengo, cliente.assiste_one_piece, cliente.eh_de_sousa, cliente.ativo),
)
```

Para todos os SELECTs, adicionar as 3 colunas e mapear no `Cliente(...)`.

Para `alterar`:
```python
cur.execute(
    """
    UPDATE clientes
    SET nome = %s, numero = %s, torce_flamengo = %s, assiste_one_piece = %s, eh_de_sousa = %s
    WHERE id = %s AND ativo = TRUE
    RETURNING id
    """,
    (cliente.nome, cliente.numero, cliente.torce_flamengo, cliente.assiste_one_piece, cliente.eh_de_sousa, cliente.id),
)
```

**Step 4: Rodar testes**

Run: `uv run pytest tests/test_cliente_repository.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add app/repositories/cliente_repository.py tests/test_cliente_repository.py
git commit -m "feat: cliente repository — campos de perfil para desconto"
```

---

## Task 4: Atualizar EstoqueRepository (TDD)

**Files:**
- Modify: `app/repositories/estoque_repository.py`
- Modify: `tests/test_estoque_repository.py`

**Step 1: Escrever testes para novos campos e filtros**

Adicionar em `tests/test_estoque_repository.py`:

```python
def test_inserir_estoque_com_categoria_e_mari(db):
    repo = EstoqueRepository()
    item = repo.inserir(
        Estoque(item="Bolo de Mari", quantidade_disponivel=10, valor=Decimal("15.00"), categoria="Doces", fabricado_em_mari=True)
    )
    recuperado = repo.exibir_um(item.id)
    assert recuperado.categoria == "Doces"
    assert recuperado.fabricado_em_mari is True


def test_buscar_por_categoria(db):
    repo = EstoqueRepository()
    repo.inserir(Estoque(item="Salgado A", quantidade_disponivel=5, valor=Decimal("5.00"), categoria="Salgados"))
    repo.inserir(Estoque(item="Bebida A", quantidade_disponivel=5, valor=Decimal("3.00"), categoria="Bebidas"))
    resultado = repo.buscar_por_filtros(categoria="Salgados")
    assert all(item.categoria == "Salgados" for item in resultado)


def test_buscar_por_faixa_preco(db):
    repo = EstoqueRepository()
    repo.inserir(Estoque(item="Barato", quantidade_disponivel=5, valor=Decimal("3.00")))
    repo.inserir(Estoque(item="Caro", quantidade_disponivel=5, valor=Decimal("50.00")))
    resultado = repo.buscar_por_filtros(valor_min=Decimal("2.00"), valor_max=Decimal("10.00"))
    assert all(Decimal("2.00") <= item.valor <= Decimal("10.00") for item in resultado)


def test_buscar_fabricado_em_mari(db):
    repo = EstoqueRepository()
    repo.inserir(Estoque(item="De Mari", quantidade_disponivel=5, valor=Decimal("5.00"), fabricado_em_mari=True))
    repo.inserir(Estoque(item="Não de Mari", quantidade_disponivel=5, valor=Decimal("5.00"), fabricado_em_mari=False))
    resultado = repo.buscar_por_filtros(fabricado_em_mari=True)
    assert all(item.fabricado_em_mari is True for item in resultado)


def test_buscar_estoque_baixo(db):
    repo = EstoqueRepository()
    repo.inserir(Estoque(item="Pouco", quantidade_disponivel=3, valor=Decimal("5.00")))
    repo.inserir(Estoque(item="Muito", quantidade_disponivel=50, valor=Decimal("5.00")))
    resultado = repo.buscar_por_filtros(estoque_baixo=True)
    assert all(item.quantidade_disponivel < 5 for item in resultado)
```

**Step 2: Rodar testes para confirmar falha**

Run: `uv run pytest tests/test_estoque_repository.py::test_inserir_estoque_com_categoria_e_mari -v`
Expected: FAIL

**Step 3: Atualizar EstoqueRepository**

1. Atualizar todos os SELECTs para incluir `categoria` e `fabricado_em_mari`.
2. Atualizar INSERT para incluir os novos campos.
3. Atualizar UPDATE (`alterar`) para incluir os novos campos.
4. Adicionar método `buscar_por_filtros`:

```python
def buscar_por_filtros(
    self,
    nome: str | None = None,
    categoria: str | None = None,
    valor_min: Decimal | None = None,
    valor_max: Decimal | None = None,
    fabricado_em_mari: bool | None = None,
    estoque_baixo: bool = False,
) -> list[Estoque]:
    query = "SELECT id, item, quantidade_disponivel, valor, categoria, fabricado_em_mari, ativo FROM estoque WHERE ativo = TRUE"
    params: list = []

    if nome:
        query += " AND item ILIKE %s"
        params.append(f"%{nome}%")
    if categoria:
        query += " AND categoria = %s"
        params.append(categoria)
    if valor_min is not None:
        query += " AND valor >= %s"
        params.append(valor_min)
    if valor_max is not None:
        query += " AND valor <= %s"
        params.append(valor_max)
    if fabricado_em_mari is not None:
        query += " AND fabricado_em_mari = %s"
        params.append(fabricado_em_mari)
    if estoque_baixo:
        query += " AND quantidade_disponivel < 5"

    query += " ORDER BY id"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    return [
        Estoque(id=r[0], item=r[1], quantidade_disponivel=r[2], valor=r[3], categoria=r[4], fabricado_em_mari=r[5], ativo=r[6])
        for r in rows
    ]
```

**Step 4: Rodar testes**

Run: `uv run pytest tests/test_estoque_repository.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add app/repositories/estoque_repository.py tests/test_estoque_repository.py
git commit -m "feat: estoque repository — categoria, fabricado_em_mari e filtros avançados"
```

---

## Task 5: Atualizar PedidoRepository (TDD)

**Files:**
- Modify: `app/repositories/pedido_repository.py`
- Modify: `tests/test_pedido_repository.py`

**Step 1: Escrever testes para vendedor, pagamento e desconto**

Adicionar em `tests/test_pedido_repository.py`:

```python
def test_inserir_pedido_com_vendedor_e_pagamento(db, cliente, itens_estoque, vendedor):
    """Pedido deve registrar vendedor_id, forma_pagamento e status_pagamento."""
    repo = PedidoRepository()
    pedido = repo.inserir(
        Pedido(
            cliente_id=cliente.id,
            vendedor_id=vendedor.id,
            forma_pagamento=FormaPagamento.PIX,
        ),
        [PedidoItem(pedido_id=0, item_id=itens_estoque[0].id, quantidade=1)],
    )
    assert pedido.vendedor_id == vendedor.id
    assert pedido.forma_pagamento == FormaPagamento.PIX
    assert pedido.status_pagamento == StatusPagamento.PENDENTE

    recuperado = repo.exibir_um(pedido.id)
    assert recuperado.vendedor_id == vendedor.id
    assert recuperado.forma_pagamento == FormaPagamento.PIX


def test_inserir_pedido_aplica_desconto_flamengo(db, itens_estoque, vendedor):
    """Cliente que torce Flamengo deve receber 5% de desconto."""
    cliente_repo = ClienteRepository()
    cliente = cliente_repo.inserir(
        Cliente(nome="Mengão", numero="777", torce_flamengo=True)
    )
    repo = PedidoRepository()
    pedido = repo.inserir(
        Pedido(cliente_id=cliente.id, vendedor_id=vendedor.id, forma_pagamento=FormaPagamento.PIX),
        [PedidoItem(pedido_id=0, item_id=itens_estoque[0].id, quantidade=2)],
    )
    valor_bruto = itens_estoque[0].valor * 2
    assert pedido.desconto == valor_bruto * Decimal("0.05")
    assert pedido.valor == valor_bruto - pedido.desconto


def test_inserir_pedido_desconto_acumula(db, itens_estoque, vendedor):
    """Cliente Flamengo + One Piece + Sousa = 15% desconto."""
    cliente_repo = ClienteRepository()
    cliente = cliente_repo.inserir(
        Cliente(nome="Full Desconto", numero="666", torce_flamengo=True, assiste_one_piece=True, eh_de_sousa=True)
    )
    repo = PedidoRepository()
    pedido = repo.inserir(
        Pedido(cliente_id=cliente.id, vendedor_id=vendedor.id, forma_pagamento=FormaPagamento.CARTAO),
        [PedidoItem(pedido_id=0, item_id=itens_estoque[0].id, quantidade=1)],
    )
    valor_bruto = itens_estoque[0].valor
    assert pedido.desconto == valor_bruto * Decimal("0.15")


def test_alterar_status_pagamento(db, cliente, itens_estoque, vendedor):
    """Confirmar pagamento deve setar pago=True."""
    repo = PedidoRepository()
    pedido = repo.inserir(
        Pedido(cliente_id=cliente.id, vendedor_id=vendedor.id, forma_pagamento=FormaPagamento.BOLETO),
        [PedidoItem(pedido_id=0, item_id=itens_estoque[0].id, quantidade=1)],
    )
    assert pedido.pago is False

    pedido.status_pagamento = StatusPagamento.CONFIRMADO
    pedido.pago = True
    atualizado = repo.alterar(pedido)
    assert atualizado.pago is True
    assert atualizado.status_pagamento == StatusPagamento.CONFIRMADO
```

Nota: será necessário criar uma fixture `vendedor` no `conftest.py`:

```python
@pytest.fixture
def vendedor(db):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM usuarios WHERE email = 'yao@lanches.com'"
            )
            row = cur.fetchone()
    from app.models.usuario import Usuario
    return Usuario(id=row[0], nome="YAO Admin", email="yao@lanches.com", senha="admin", numero="00000000000", role="admin")
```

**Step 2: Rodar testes para confirmar falha**

Run: `uv run pytest tests/test_pedido_repository.py::test_inserir_pedido_com_vendedor_e_pagamento -v`
Expected: FAIL

**Step 3: Atualizar PedidoRepository**

1. `inserir`: chamar `calcular_desconto` via SQL (`SELECT calcular_desconto(%s)`), calcular valor com desconto, incluir `vendedor_id`, `forma_pagamento`, `status_pagamento`, `desconto` no INSERT.
2. Todos os SELECTs (`listar_todos`, `exibir_um`): incluir os novos campos.
3. `alterar`: incluir `status_pagamento` no UPDATE, e quando `status_pagamento = CONFIRMADO` setar `pago = True`.

Exemplo chave no `inserir`, após `_validar_e_calcular`:

```python
cur.execute("SELECT calcular_desconto(%s)", (pedido.cliente_id,))
percentual_desconto = cur.fetchone()[0] or Decimal("0")
pedido.desconto = (pedido.valor * percentual_desconto / Decimal("100")).quantize(Decimal("0.01"))
pedido.valor = pedido.valor - pedido.desconto
```

Exemplo para SELECT:
```python
cur.execute("""
    SELECT id, cliente_id, data, estado, valor, pago,
           vendedor_id, forma_pagamento, status_pagamento, desconto
    FROM pedidos WHERE id = %s
""", (pedido_id,))
```

**Step 4: Rodar todos os testes de pedido**

Run: `uv run pytest tests/test_pedido_repository.py -v`
Expected: ALL PASS (os antigos podem precisar de ajustes mínimos para os novos campos)

**Step 5: Commit**

```bash
git add app/repositories/pedido_repository.py tests/test_pedido_repository.py tests/conftest.py
git commit -m "feat: pedido repository — vendedor, pagamento, desconto via FUNCTION"
```

---

## Task 6: Atualizar API (DTOs + Endpoints)

**Files:**
- Modify: `app/main.py`

**Step 1: Atualizar DTOs**

```python
# ClienteCreate — adicionar campos de perfil
class ClienteCreate(BaseModel):
    nome: str = Field(min_length=1)
    numero: str = Field(min_length=1)
    torce_flamengo: bool = False
    assiste_one_piece: bool = False
    eh_de_sousa: bool = False

# ClienteResponse — adicionar campos de perfil
class ClienteResponse(BaseModel):
    id: int
    nome: str
    numero: str
    torce_flamengo: bool
    assiste_one_piece: bool
    eh_de_sousa: bool
    ativo: bool

# EstoqueCreate — adicionar categoria e fabricado_em_mari
class EstoqueCreate(BaseModel):
    item: str = Field(min_length=1)
    quantidade_disponivel: int = Field(ge=0)
    valor: Decimal = Field(gt=0)
    categoria: str = "Geral"
    fabricado_em_mari: bool = False

# EstoqueResponse — adicionar campos
class EstoqueResponse(BaseModel):
    id: int
    item: str
    quantidade_disponivel: int
    valor: float
    categoria: str
    fabricado_em_mari: bool
    ativo: bool

# PedidoCreate — adicionar vendedor e pagamento
class PedidoCreate(BaseModel):
    cliente_id: int
    vendedor_id: int | None = None
    forma_pagamento: FormaPagamento | None = None
    estado: EstadoPedido = EstadoPedido.EM_ANDAMENTO
    pago: bool = False
    itens: list[PedidoItemCreate]

# PedidoUpdate — adicionar status_pagamento
class PedidoUpdate(BaseModel):
    estado: EstadoPedido | None = None
    pago: bool | None = None
    status_pagamento: StatusPagamento | None = None

# PedidoResponse — adicionar campos
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

# Novo DTO para relatório de vendas por vendedor
class VendaVendedorResponse(BaseModel):
    vendedor_id: int
    vendedor_nome: str
    mes: str
    total_pedidos: int
    valor_total: float
    desconto_total: float
    pagamentos_confirmados: int
```

**Step 2: Atualizar endpoint GET /estoque com filtros**

```python
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
```

**Step 3: Adicionar endpoint GET /relatorios/vendas-vendedor**

```python
@app.get("/relatorios/vendas-vendedor", response_model=list[VendaVendedorResponse])
def relatorio_vendas_vendedor() -> list[VendaVendedorResponse]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT vendedor_id, vendedor_nome, mes, total_pedidos, valor_total, desconto_total, pagamentos_confirmados FROM vw_vendas_por_vendedor")
            rows = cur.fetchall()
    return [
        VendaVendedorResponse(
            vendedor_id=r[0], vendedor_nome=r[1], mes=r[2].isoformat(),
            total_pedidos=r[3], valor_total=float(r[4]),
            desconto_total=float(r[5]), pagamentos_confirmados=r[6],
        )
        for r in rows
    ]
```

**Step 4: Atualizar funções helper e endpoints de criação**

Atualizar `_cliente_to_response`, `_estoque_to_response`, `_build_pedido_response`, `criar_cliente`, `alterar_cliente`, `criar_item_estoque`, `alterar_item_estoque`, `criar_pedido`, `alterar_pedido` para passar os novos campos.

**Step 5: Rodar testes da API**

Run: `uv run pytest tests/test_api.py -v`
Expected: ALL PASS (pode precisar atualizar payloads nos testes)

**Step 6: Commit**

```bash
git add app/main.py
git commit -m "feat: API parte 2 — DTOs, filtros de estoque, relatório por vendedor"
```

---

## Task 7: Atualizar Testes da API

**Files:**
- Modify: `tests/test_api.py`
- Modify: `tests/conftest.py`

**Step 1: Atualizar testes existentes para novos campos**

Atualizar os payloads de criação de clientes para incluir `torce_flamengo`, `assiste_one_piece`, `eh_de_sousa`.
Atualizar payloads de estoque para incluir `categoria`, `fabricado_em_mari`.
Atualizar payloads de pedidos para incluir `vendedor_id`, `forma_pagamento`.
Verificar que os responses contêm os novos campos.

**Step 2: Adicionar testes novos**

```python
def test_filtrar_estoque_por_categoria(client, admin_login):
    # criar itens com categorias diferentes, filtrar
    ...

def test_filtrar_estoque_por_faixa_preco(client, admin_login):
    ...

def test_filtrar_estoque_baixo(client, admin_login):
    ...

def test_relatorio_vendas_vendedor(client, admin_login):
    response = client.get("/relatorios/vendas-vendedor")
    assert response.status_code == 200

def test_pedido_com_desconto_flamengo(client, admin_login):
    # criar cliente flamenguista, criar pedido, verificar desconto
    ...
```

**Step 3: Rodar testes**

Run: `uv run pytest tests/ -v`
Expected: ALL PASS

**Step 4: Commit**

```bash
git add tests/
git commit -m "test: atualizar testes para parte 2"
```

---

## Task 8: Atualizar Frontend — Types e API Client

**Files:**
- Modify: `frontend/src/lib/types.ts`

**Step 1: Atualizar types.ts**

```typescript
export type EstadoPedido = "EM_ANDAMENTO" | "PRONTO" | "ENTREGUE" | "CANCELADO";
export type FormaPagamento = "CARTAO" | "BOLETO" | "PIX" | "BERRIES";
export type StatusPagamento = "PENDENTE" | "CONFIRMADO" | "REJEITADO";

export interface Cliente {
  id: number;
  nome: string;
  numero: string;
  torce_flamengo: boolean;
  assiste_one_piece: boolean;
  eh_de_sousa: boolean;
  ativo: boolean;
}

export interface EstoqueItem {
  id: number;
  item: string;
  quantidade_disponivel: number;
  valor: number;
  categoria: string;
  fabricado_em_mari: boolean;
  ativo: boolean;
}

export interface PedidoItem {
  id: number;
  pedido_id: number;
  item_id: number;
  quantidade: number;
  valor_unitario: number;
}

export interface Pedido {
  id: number;
  cliente_id: number;
  cliente_nome: string;
  data: string;
  estado: EstadoPedido;
  valor: number;
  pago: boolean;
  vendedor_id: number | null;
  vendedor_nome: string | null;
  forma_pagamento: FormaPagamento | null;
  status_pagamento: StatusPagamento;
  desconto: number;
  itens: PedidoItem[];
}

export interface RelatorioVendas {
  total_pedidos: number;
  valor_total: number;
  pedidos_pagos: number;
  pedidos_nao_pagos: number;
  ticket_medio: number;
}

export interface RelatorioEstoque {
  itens_cadastrados: number;
  quantidade_total: number;
  valor_inventario: number;
  itens_sem_estoque: number;
}

export interface RelatorioClientes {
  total_clientes: number;
  clientes_com_pedidos_ativos: number;
  clientes_sem_pedidos: number;
}

export interface VendaVendedor {
  vendedor_id: number;
  vendedor_nome: string;
  mes: string;
  total_pedidos: number;
  valor_total: number;
  desconto_total: number;
  pagamentos_confirmados: number;
}
```

**Step 2: Commit**

```bash
git add frontend/src/lib/types.ts
git commit -m "feat: frontend types para parte 2"
```

---

## Task 9: Atualizar Frontend — Página de Clientes

**Files:**
- Modify: `frontend/src/app/dashboard/clientes/page.tsx`

**Step 1: Adicionar campos de perfil ao formulário de criação/edição**

No formulário de criar/editar cliente, adicionar 3 checkboxes:
- "Torce pro Flamengo" (`torce_flamengo`)
- "Assiste One Piece" (`assiste_one_piece`)
- "É de Sousa" (`eh_de_sousa`)

No payload do POST/PUT, incluir estes campos.

**Step 2: Mostrar badges de desconto na tabela/detalhes**

Na tabela de clientes, mostrar badges coloridos indicando quais descontos o cliente tem.
No painel de detalhes, mostrar os campos de perfil.

**Step 3: Testar manualmente**

- Criar cliente com flags de desconto → verificar que badges aparecem
- Editar cliente → verificar que flags são mantidas

**Step 4: Commit**

```bash
git add frontend/src/app/dashboard/clientes/page.tsx
git commit -m "feat: frontend clientes — campos de perfil desconto"
```

---

## Task 10: Atualizar Frontend — Página de Estoque

**Files:**
- Modify: `frontend/src/app/dashboard/estoque/page.tsx`

**Step 1: Adicionar campos de categoria e fabricado_em_mari ao formulário**

- Select de `categoria` com opções: "Geral", "Salgados", "Bebidas", "Doces", "Outros"
- Checkbox "Fabricado em Mari" (`fabricado_em_mari`)

**Step 2: Adicionar filtros avançados**

Na barra de busca, adicionar:
- Dropdown de categoria
- Inputs de faixa de preço (min / max)
- Checkbox "Fabricado em Mari"
- Checkbox "Estoque Baixo (< 5 unidades)" (apenas para admin/funcionário)

Estes filtros são passados como query params ao `GET /estoque`.

**Step 3: Mostrar novos campos na tabela**

- Coluna "Categoria"
- Badge "Mari" se `fabricado_em_mari` é true

**Step 4: Testar manualmente**

- Criar item com categoria + fabricado_em_mari → verificar exibição
- Filtrar por categoria, preço, Mari, estoque baixo

**Step 5: Commit**

```bash
git add frontend/src/app/dashboard/estoque/page.tsx
git commit -m "feat: frontend estoque — categoria, Mari e filtros avançados"
```

---

## Task 11: Atualizar Frontend — Página de Pedidos (Dashboard)

**Files:**
- Modify: `frontend/src/app/dashboard/pedidos/page.tsx`

**Step 1: Adicionar vendedor e pagamento ao formulário de criação**

No formulário "Novo pedido":
- Select "Forma de Pagamento": CARTAO, BOLETO, PIX, BERRIES
- O `vendedor_id` é automaticamente o usuário logado (pegar do `AuthContext`)

No payload do POST, incluir `vendedor_id` e `forma_pagamento`.

**Step 2: Adicionar status de pagamento ao painel de edição**

No painel de editar pedido:
- Select "Status Pagamento": PENDENTE, CONFIRMADO, REJEITADO
- Quando muda para CONFIRMADO, o `pago` é setado para `true` automaticamente

**Step 3: Mostrar novos campos na tabela/detalhes**

- Coluna/badge "Forma Pgto"
- Coluna/badge "Status Pgto" (com cores: amarelo=PENDENTE, verde=CONFIRMADO, vermelho=REJEITADO)
- Mostrar "Desconto: R$ X,XX" nos detalhes quando > 0
- Mostrar "Vendedor: Nome" nos detalhes

**Step 4: Testar manualmente**

- Criar pedido com forma de pagamento → verificar que aparece
- Alterar status pagamento → verificar badge muda

**Step 5: Commit**

```bash
git add frontend/src/app/dashboard/pedidos/page.tsx
git commit -m "feat: frontend pedidos — vendedor, pagamento e desconto"
```

---

## Task 12: Atualizar Frontend — Relatório de Vendas por Vendedor

**Files:**
- Modify: `frontend/src/app/dashboard/relatorios/page.tsx`

**Step 1: Adicionar seção de vendas por vendedor**

Adicionar um novo card/seção ao relatórios page:
- Título: "Vendas por Vendedor (Mensal)"
- Chamar `GET /relatorios/vendas-vendedor`
- Exibir tabela com colunas: Vendedor, Mês, Total Pedidos, Valor Total, Desconto Total, Pgtos Confirmados

**Step 2: Testar manualmente**

- Criar pedidos com vendedor → verificar que o relatório lista corretamente

**Step 3: Commit**

```bash
git add frontend/src/app/dashboard/relatorios/page.tsx
git commit -m "feat: frontend relatório de vendas por vendedor"
```

---

## Task 13: Atualizar Frontend — Página de Pedido (Cliente)

**Files:**
- Modify: `frontend/src/app/pedido/page.tsx`

**Step 1: Adicionar seleção de forma de pagamento**

No checkout (antes de "Enviar Pedido"):
- Select "Forma de Pagamento": Cartão, Boleto, Pix, Berries
- Obrigatório para enviar

**Step 2: Mostrar desconto no resumo**

Se o cliente logado tem flags de desconto:
- Mostrar "Desconto: X%" no carrinho
- Mostrar valor com desconto vs valor cheio

**Step 3: Mostrar status de pagamento nos pedidos**

Na lista "Meus Pedidos", mostrar badge do status_pagamento (PENDENTE, CONFIRMADO, REJEITADO).

**Step 4: Testar manualmente**

- Login como cliente com desconto → verificar que desconto aparece no carrinho
- Enviar pedido com forma de pagamento → verificar no dashboard

**Step 5: Commit**

```bash
git add frontend/src/app/pedido/page.tsx
git commit -m "feat: frontend pedido cliente — pagamento e desconto"
```

---

## Task 14: Atualizar AuthContext para user_id no pedido

**Files:**
- Modify: `frontend/src/contexts/AuthContext.tsx`
- Modify: `frontend/src/lib/types.ts` (se necessário)

**Step 1: Garantir que o AuthContext expõe o `user.id` para uso como vendedor_id**

Verificar que o `User` no AuthContext já tem `id`. No login response, o backend já retorna `id`. Garantir que está mapeado corretamente.

**Step 2: Commit (se houve mudança)**

```bash
git add frontend/src/contexts/AuthContext.tsx
git commit -m "fix: auth context expõe user id para vendedor"
```

---

## Task 15: Rodar Todos os Testes + Verificação Final

**Step 1: Rodar backend tests**

Run: `uv run pytest tests/ -v`
Expected: ALL PASS

**Step 2: Verificar schema no banco**

Run (dentro do container): `psql -U postgres -d marmitaria -c "\d pedidos"` e verificar que os novos campos existem.
Run: `psql -U postgres -d marmitaria -c "SELECT * FROM vw_vendas_por_vendedor LIMIT 5"`
Run: `psql -U postgres -d marmitaria -c "SELECT calcular_desconto(1)"`

**Step 3: Verificar frontend compila**

Run: `cd frontend && npm run build`
Expected: build sem erros

**Step 4: Commit final**

```bash
git add -A
git commit -m "chore: verificação final parte 2 completa"
```

---

## Resumo de Entregas da Parte 2

| Entrega | Arquivo(s) |
|---|---|
| Vendedor no pedido | `pedidos.vendedor_id` → `usuarios(id)` |
| Forma de pagamento | ENUM `forma_pagamento` + coluna em pedidos |
| Status de confirmação | ENUM `status_pagamento` + coluna em pedidos |
| Desconto Flamengo/One Piece/Sousa | `clientes` novos campos + FUNCTION `calcular_desconto` |
| Categoria + Mari no estoque | `estoque.categoria`, `estoque.fabricado_em_mari` |
| Filtros avançados de estoque | `buscar_por_filtros()` + query params na API |
| Filtro estoque baixo (< 5) | Parâmetro `estoque_baixo` no filtro |
| Relatório mensal por vendedor | VIEW `vw_vendas_por_vendedor` + endpoint |
| VIEW obrigatória | `vw_vendas_por_vendedor` |
| STORED PROCEDURE obrigatória | `calcular_desconto()` |
| Índices novos | `idx_pedidos_vendedor`, `idx_estoque_categoria`, `idx_pedidos_data` |
| Frontend atualizado | Todas as telas refletem novos campos |
