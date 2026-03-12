# Sistema de Marmitaria - Projeto de Banco de Dados

Este projeto foi desenvolvido para a disciplina de Banco de Dados e tem como objetivo implementar um sistema CRUD completo para o gerenciamento de uma marmitaria.

A aplicação simula o funcionamento de um sistema de vendas simples, permitindo o cadastro de clientes, marmitas e pedidos, além de consultas e geração de relatórios.

---

## Primeiros passos

O projeto usa **Dev Containers**. Ao abrir no VS Code/Cursor, o ambiente é configurado automaticamente com Python 3.12, PostgreSQL, UV, lazygit e opencode.

### 1. Abrir o container

Na paleta de comandos (`Ctrl+Shift+P` / `Cmd+Shift+P`), selecione:

```
Dev Containers: Reopen in Container
```

### 2. Configurar o GitHub (obrigatório para desenvolvimento)

Ao abrir o container, o terminal exibirá um aviso caso o GitHub ainda não esteja configurado. Execute:

```bash
gh auth login
```

Siga as instruções e escolha:
- **GitHub.com**
- **HTTPS** (recomendado) ou SSH
- **Login via browser** (mais fácil)

Após autenticar, push e pull funcionarão normalmente.

### 3. Instalar dependências

As dependências Python são instaladas automaticamente via `uv sync` na criação do container. Para instalar manualmente:

```bash
uv sync
```

Para adicionar novos pacotes:

```bash
uv add nome-do-pacote
```

---

## Modelagem — Diagrama UML de Classes

```mermaid
classDiagram
    direction TB

    class Cliente {
        +int id
        +str nome
        +str numero
        +inserir()
        +alterar()
        +remover()
        +buscar_por_nome(nome) List
        +listar_todos() List
        +exibir(id)
    }

    class Pedido {
        +int id
        +int cliente_id
        +TamanhoMarmita tamanho
        +date data
        +EstadoPedido estado
        +Decimal valor
        +bool pago
        +inserir()
        +alterar()
        +remover()
        +buscar(id)
        +listar_todos() List
        +listar_por_cliente(cliente_id) List
        +exibir(id)
        +atualizar_estado(estado)
        +marcar_pago()
    }

    class Estoque {
        +int id
        +int quantidade_disponivel
        +Decimal valor_marmita
        +atualizar_quantidade(delta)
        +atualizar_valor(valor)
        +exibir()
    }

    class TamanhoMarmita {
        <<enumeration>>
        P
        M
        G
    }

    class EstadoPedido {
        <<enumeration>>
        EM_ANDAMENTO
        PRONTO
        ENTREGUE
    }

    class Database {
        -str url
        +get_connection()
        +close()
    }

    Cliente "1" --> "0..*" Pedido : realiza
    Pedido --> "1" TamanhoMarmita : tamanho
    Pedido --> "1" EstadoPedido : estado
    Pedido "0..*" ..> "1" Estoque : consome ao criar
    Cliente ..> Database : usa
    Pedido ..> Database : usa
    Estoque ..> Database : usa
```

### Descrição das entidades

| Entidade | Tabela | Descrição |
|---|---|---|
| `Cliente` | `clientes` | Cadastro de clientes da marmitaria |
| `Pedido` | `pedidos` | Pedidos realizados pelos clientes |
| `Estoque` | `estoque` | Controle de marmitas disponíveis e preço (Yao) |
| `TamanhoMarmita` | — | Enum: `P`, `M`, `G` |
| `EstadoPedido` | — | Enum: `EM_ANDAMENTO`, `PRONTO`, `ENTREGUE` |
| `Database` | — | Gerencia a conexão com o PostgreSQL |
