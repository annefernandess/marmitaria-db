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
| Campo      | Tipo           | Restrições                              |
|------------|----------------|-----------------------------------------|
| id         | SERIAL         | PK                                      |
| cliente_id | INT            | FK → clientes(id)                       |
| tamanho    | ENUM           | P, M, G — NOT NULL                      |
| data       | DATE           | NOT NULL, default hoje                  |
| estado     | ENUM           | EM_ANDAMENTO, PRONTO, ENTREGUE          |
| valor      | NUMERIC(10,2)  | NOT NULL                                |
| pago       | BOOLEAN        | NOT NULL, default false                 |

#### `estoque` (tabela da loja Yao — única linha de configuração)
| Campo                  | Tipo          | Restrições  |
|------------------------|---------------|-------------|
| id                     | SERIAL        | PK          |
| quantidade_disponivel  | INT           | NOT NULL    |
| valor_marmita          | NUMERIC(10,2) | NOT NULL    |

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
- `Pedido`: ao criar, decrementar `estoque.quantidade_disponivel`
- `Estoque`: atualizar quantidade disponível e valor da marmita

---

## Arquitetura em camadas

```
frontend/          → a definir (stack ainda não decidida)
app/
  models/          → Classes de domínio (dataclasses ou Pydantic)
  repositories/    → Acesso ao banco (ClienteRepository, PedidoRepository, EstoqueRepository)
  services/        → Regras de negócio (validações, lógica de estoque)
  routers/         → Rotas FastAPI (endpoints REST)
  database.py      → Conexão com PostgreSQL via psycopg2
  main.py          → Entrypoint FastAPI
```

---

## Regras de negócio

1. Não é possível criar um pedido se `estoque.quantidade_disponivel == 0`.
2. O `valor` do pedido é herdado de `estoque.valor_marmita` no momento da criação.
3. Um cliente só pode ser removido se não tiver pedidos vinculados.
4. O estado do pedido só pode avançar em ordem: `EM_ANDAMENTO` → `PRONTO` → `ENTREGUE`.

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
