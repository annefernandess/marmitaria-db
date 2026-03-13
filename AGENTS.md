# AGENTS.md — Contexto do Projeto Marmitaria

Este arquivo fornece contexto persistente para agentes de IA (Cursor, opencode, etc.) sobre a arquitetura, regras e decisões do projeto.

---

## Visão Geral

Sistema CRUD completo para gerenciamento de uma marmitaria chamada **Yao**.
Projeto acadêmico da disciplina de Banco de Dados.

**Stack:**
- **Backend:** Python com FastAPI
- **Banco de dados:** PostgreSQL 16
- **Gerenciador de pacotes:** UV (`uv sync` / `uv add`)
- **ORM / acesso ao banco:** psycopg2 (raw SQL ou SQLAlchemy — a definir)
- **Frontend:** A definir
- **Ambiente:** Dev Container (Docker)

---

## Domínio

### Entidades e tabelas

#### `clientes`
| Campo  | Tipo    | Restrições     |
|--------|---------|----------------|
| id     | SERIAL  | PK             |
| nome   | VARCHAR | NOT NULL       |
| numero | VARCHAR | NOT NULL       |

#### `pedidos`
| Campo      | Tipo          | Restrições                              |
|------------|---------------|-----------------------------------------|
| id         | SERIAL        | PK                                      |
| cliente_id | INT           | FK → clientes(id)                       |
| data       | DATE          | NOT NULL, default hoje                  |
| estado     | estado_pedido | EM_ANDAMENTO, PRONTO, ENTREGUE          |
| valor      | NUMERIC(10,2) | NOT NULL, default 0                     |
| pago       | BOOLEAN       | NOT NULL, default false                 |

#### `pedido_itens` (N:N entre pedidos e estoque)
| Campo      | Tipo   | Restrições                                     |
|------------|--------|------------------------------------------------|
| id         | SERIAL | PK                                             |
| pedido_id  | INT    | FK → pedidos(id) ON DELETE CASCADE             |
| item_id    | INT    | FK → estoque(id)                               |
| quantidade | INT    | NOT NULL, default 1, > 0                       |

#### `estoque` (cardápio de itens da loja Yao)
| Campo                 | Tipo          | Restrições              |
|-----------------------|---------------|-------------------------|
| id                    | SERIAL        | PK                      |
| item                  | VARCHAR(255)  | NOT NULL                |
| quantidade_disponivel | INT           | NOT NULL, >= 0          |
| valor                 | NUMERIC(10,2) | NOT NULL, > 0           |

---

## Especificações do projeto (requisitos acadêmicos)

1. Sistema CRUD com as operações: **Inserir, Alterar, Pesquisar por nome, Remover, Listar todos, Exibir um**
2. Modelagem das classes com **diagrama UML** — já realizado no `README.md`
3. Utilizar uma **classe que gerencia as operações CRUD** (ex: `Repository` ou `Manager` por entidade)
4. O objeto principal deve ter **pelo menos 4 atributos** — `Pedido` tem 6, `Estoque` tem 4 ✓
5. Usar bastante **métodos** nas classes
6. Gerar **relatórios** com resumo das informações:
   - Relatório de vendas (total de pedidos, valor total, pedidos pagos/não pagos)
   - Relatório de estoque (itens cadastrados, quantidade disponível, valor de inventário)
   - Relatório de clientes (total de clientes, clientes com pedidos ativos)

---

## Operações CRUD obrigatórias

Cada entidade deve suportar:

| Operação           | Descrição                                   |
|--------------------|---------------------------------------------|
| Inserir            | Cadastrar novo registro                     |
| Alterar            | Editar campos de um registro existente      |
| Remover            | Deletar por ID                              |
| Pesquisar por nome | Busca parcial/exata por nome (clientes)     |
| Listar todos       | Retornar todos os registros                 |
| Exibir um          | Retornar um registro por ID                 |

**Operações extras:**
- `Pedido`: atualizar estado (`EM_ANDAMENTO` → `PRONTO` → `ENTREGUE`) e marcar como pago
- `Pedido`: ao criar, para cada item em `pedido_itens` decrementar `estoque.quantidade_disponivel`
- `Estoque`: atualizar quantidade disponível e valor do item

---

## Arquitetura em camadas

```
frontend/          → a definir (stack ainda não decidida)
app/
  models/          → Classes de domínio (dataclasses ou Pydantic)
  repositories/    → Acesso ao banco (ClienteRepository, PedidoRepository, PedidoItemRepository, EstoqueRepository)
  services/        → Regras de negócio (validações, lógica de estoque)
  routers/         → Rotas FastAPI (endpoints REST)
  database.py      → Conexão com PostgreSQL via psycopg2
  main.py          → Entrypoint FastAPI
```

---

## Regras de negócio

1. Não é possível adicionar um item ao pedido se `estoque.quantidade_disponivel < quantidade_solicitada`.
2. O `valor` do pedido é calculado como `SUM(pedido_itens.quantidade * estoque.valor)` no momento da criação.
3. Ao criar um pedido, decrementar `estoque.quantidade_disponivel` para cada item; ao remover, restaurar.
4. Um cliente só pode ser removido se não tiver pedidos vinculados.
5. O estado do pedido só pode avançar em ordem: `EM_ANDAMENTO` → `PRONTO` → `ENTREGUE`.

---

## Metodologia: TDD (Test-Driven Development)

**Este projeto segue TDD estritamente. Nenhuma feature deve ser implementada sem um teste escrito antes.**

### Ciclo obrigatório para qualquer nova funcionalidade

1. **Red** — escreva o teste para a feature. Rode e confirme que ele falha.
2. **Green** — implemente o mínimo de código para o teste passar.
3. **Refactor** — limpe o código sem quebrar os testes.

> Nunca escreva código de produção sem um teste vermelho antes. Se não há teste, não há feature.

### Rodando os testes

```bash
# Todos os testes
uv run pytest tests/ -v

# Um arquivo específico
uv run pytest tests/test_cliente_repository.py -v

# Um teste específico
uv run pytest tests/test_pedido_repository.py::test_inserir_calcula_valor_total -v
```

### Onde ficam os testes

```
tests/
  conftest.py                   → fixtures compartilhadas (conexão DB com rollback automático)
  test_cliente_repository.py
  test_estoque_repository.py
  test_pedido_repository.py
```

### Convenção de nomes

- Arquivos: `test_<nome_do_modulo>.py`
- Funções: `test_<metodo>_<comportamento_esperado>` (ex: `test_inserir_calcula_valor_total`)

---

## Variáveis de ambiente

| Variável       | Valor padrão (container)                          |
|----------------|---------------------------------------------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@db:5432/marmitaria` |

---

## Convenções de código

- Python 3.12+
- Tipagem explícita em todas as funções
- Nomes de variáveis e funções em português (domínio) ou inglês (infraestrutura)
- Enums Python espelham os tipos ENUM do PostgreSQL
- Commits em português, mensagens curtas e descritivas
