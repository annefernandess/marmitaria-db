from decimal import Decimal

from fastapi.testclient import TestClient
import pytest

from app.models.cliente import Cliente
from app.models.estoque import Estoque
from app.models.pedido import Pedido
from app.models.pedido_item import PedidoItem
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.estoque_repository import EstoqueRepository
from app.repositories.pedido_repository import PedidoRepository


@pytest.fixture
def client(db):
    from app.main import create_app

    return TestClient(create_app())


def test_healthcheck_retorna_status_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_auth_cadastra_usuario_e_retorna_cliente_vinculado(client, db):
    response = client.post(
        "/auth/register",
        json={
            "nome": "Maria Cliente",
            "email": "maria@cliente.com",
            "senha": "123456",
            "numero": "11999990001",
        },
    )

    assert response.status_code == 201
    assert response.json()["nome"] == "Maria Cliente"
    assert response.json()["email"] == "maria@cliente.com"
    assert response.json()["numero"] == "11999990001"
    assert response.json()["role"] == "user"
    assert response.json()["cliente_id"] is not None

    with db.cursor() as cur:
        cur.execute(
            "SELECT nome, numero FROM clientes WHERE id = %s",
            (response.json()["cliente_id"],),
        )
        assert cur.fetchone() == ("Maria Cliente", "11999990001")


def test_auth_login_retorna_usuario_cadastrado(client):
    registered = client.post(
        "/auth/register",
        json={
            "nome": "João Login",
            "email": "joao@login.com",
            "senha": "abc123",
            "numero": "11888880002",
        },
    )

    response = client.post(
        "/auth/login",
        json={"email": "joao@login.com", "senha": "abc123"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == registered.json()["id"]
    assert response.json()["nome"] == "João Login"
    assert response.json()["email"] == "joao@login.com"
    assert response.json()["numero"] == "11888880002"
    assert response.json()["cliente_id"] == registered.json()["cliente_id"]


def test_auth_nao_permita_email_duplicado(client):
    client.post(
        "/auth/register",
        json={
            "nome": "Primeiro",
            "email": "duplicado@cliente.com",
            "senha": "123456",
            "numero": "11777770003",
        },
    )

    response = client.post(
        "/auth/register",
        json={
            "nome": "Segundo",
            "email": "duplicado@cliente.com",
            "senha": "654321",
            "numero": "11666660004",
        },
    )

    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()


def test_auth_login_admin_seedado(client):
    response = client.post(
        "/auth/login",
        json={"email": "yao@lanches.com", "senha": "admin"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    assert response.json()["cliente_id"] is None


def test_clientes_cria_lista_busca_e_exibe_um(client):
    created = client.post(
        "/clientes",
        json={"nome": "Maria Silva", "numero": "11999990001"},
    )

    assert created.status_code == 201
    assert created.json()["nome"] == "Maria Silva"
    assert created.json()["numero"] == "11999990001"
    assert created.json()["ativo"] is True

    listed = client.get("/clientes")

    assert listed.status_code == 200
    assert len(listed.json()) == 1

    filtered = client.get("/clientes", params={"nome": "maria"})

    assert filtered.status_code == 200
    assert filtered.json()[0]["id"] == created.json()["id"]

    shown = client.get(f"/clientes/{created.json()['id']}")

    assert shown.status_code == 200
    assert shown.json()["id"] == created.json()["id"]


def test_estoque_cria_lista_busca_e_exibe_um(client):
    created = client.post(
        "/estoque",
        json={
            "item": "Coxinha de Frango",
            "quantidade_disponivel": 15,
            "valor": 6.5,
        },
    )

    assert created.status_code == 201
    assert created.json()["item"] == "Coxinha de Frango"
    assert created.json()["quantidade_disponivel"] == 15
    assert created.json()["valor"] == 6.5

    listed = client.get("/estoque")

    assert listed.status_code == 200
    assert len(listed.json()) == 1

    filtered = client.get("/estoque", params={"nome": "coxinha"})

    assert filtered.status_code == 200
    assert filtered.json()[0]["id"] == created.json()["id"]

    shown = client.get(f"/estoque/{created.json()['id']}")

    assert shown.status_code == 200
    assert shown.json()["id"] == created.json()["id"]


def test_pedidos_cria_lista_exibe_e_atualiza(client, db):
    cliente = ClienteRepository().inserir(Cliente(nome="Pedro", numero="11999990002"))
    item = EstoqueRepository().inserir(
        Estoque(item="Pastel de Carne", quantidade_disponivel=10, valor=Decimal("8.00"))
    )

    created = client.post(
        "/pedidos",
        json={
            "cliente_id": cliente.id,
            "itens": [{"item_id": item.id, "quantidade": 2}],
        },
    )

    assert created.status_code == 201
    assert created.json()["cliente_id"] == cliente.id
    assert created.json()["cliente_nome"] == "Pedro"
    assert created.json()["valor"] == 16.0
    assert created.json()["itens"][0]["quantidade"] == 2
    assert created.json()["itens"][0]["valor_unitario"] == 8.0

    listed = client.get("/pedidos")

    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["cliente_nome"] == "Pedro"

    shown = client.get(f"/pedidos/{created.json()['id']}")

    assert shown.status_code == 200
    assert shown.json()["id"] == created.json()["id"]

    updated = client.patch(
        f"/pedidos/{created.json()['id']}",
        json={"estado": "PRONTO", "pago": True},
    )

    assert updated.status_code == 200
    assert updated.json()["estado"] == "PRONTO"
    assert updated.json()["pago"] is True

    with db.cursor() as cur:
        cur.execute("SELECT quantidade_disponivel FROM estoque WHERE id = %s", (item.id,))
        assert cur.fetchone()[0] == 8


def test_relatorios_retorna_resumos_de_vendas_estoque_e_clientes(client):
    cliente_repo = ClienteRepository()
    estoque_repo = EstoqueRepository()
    pedido_repo = PedidoRepository()

    ana = cliente_repo.inserir(Cliente(nome="Ana", numero="11111111111"))
    bruno = cliente_repo.inserir(Cliente(nome="Bruno", numero="22222222222"))

    item_a = estoque_repo.inserir(
        Estoque(item="Coxinha", quantidade_disponivel=10, valor=Decimal("5.00"))
    )
    item_b = estoque_repo.inserir(
        Estoque(item="Kibe", quantidade_disponivel=0, valor=Decimal("7.00"))
    )

    pedido_repo.inserir(
        Pedido(cliente_id=ana.id, pago=True),
        [PedidoItem(pedido_id=0, item_id=item_a.id, quantidade=2)],
    )

    vendas = client.get("/relatorios/vendas")
    estoque = client.get("/relatorios/estoque")
    clientes = client.get("/relatorios/clientes")

    assert vendas.status_code == 200
    assert vendas.json() == {
        "total_pedidos": 1,
        "valor_total": 10.0,
        "pedidos_pagos": 1,
        "pedidos_nao_pagos": 0,
        "ticket_medio": 10.0,
    }

    assert estoque.status_code == 200
    assert estoque.json() == {
        "itens_cadastrados": 2,
        "quantidade_total": 8,
        "valor_inventario": 40.0,
        "itens_sem_estoque": 1,
    }

    assert clientes.status_code == 200
    assert clientes.json() == {
        "total_clientes": 2,
        "clientes_com_pedidos_ativos": 1,
        "clientes_sem_pedidos": 1,
    }


def test_api_retorna_400_quando_regra_de_negocio_e_violada(client):
    cliente = ClienteRepository().inserir(Cliente(nome="Erro", numero="33333333333"))

    response = client.post(
        "/pedidos",
        json={"cliente_id": cliente.id, "itens": []},
    )

    assert response.status_code == 400
    assert "pelo menos um item" in response.json()["detail"]
