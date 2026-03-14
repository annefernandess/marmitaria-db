from decimal import Decimal

import pytest

from app.models.cliente import Cliente
from app.models.estoque import Estoque
from app.models.pedido import Pedido
from app.models.pedido_item import PedidoItem
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.estoque_repository import EstoqueRepository
from app.repositories.pedido_item_repository import PedidoItemRepository
from app.repositories.pedido_repository import PedidoRepository


@pytest.fixture
def repo():
    return PedidoItemRepository()


@pytest.fixture
def cliente(db):
    return ClienteRepository().inserir(Cliente(nome="Cliente Teste", numero="11900000000"))


@pytest.fixture
def item_estoque(db):
    return EstoqueRepository().inserir(
        Estoque(item="Marmita Frango", quantidade_disponivel=10, valor=Decimal("15.00"))
    )


def test_listar_todos_retorna_itens_do_pedido(db, repo, cliente, item_estoque):
    pedido_repo = PedidoRepository()
    pedido = pedido_repo.inserir(
        Pedido(cliente_id=cliente.id),
        [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=2)],
    )

    itens = repo.listar_todos()

    assert len(itens) == 1
    assert itens[0].pedido_id == pedido.id
    assert itens[0].item_id == item_estoque.id
    assert itens[0].quantidade == 2
    assert isinstance(itens[0].id, int)


def test_remover_item_restaura_estoque(db, repo, cliente, item_estoque):
    pedido_repo = PedidoRepository()
    pedido_repo.inserir(
        Pedido(cliente_id=cliente.id),
        [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=4)],
    )

    itens = repo.listar_todos()
    assert len(itens) == 1

    repo.remover(itens[0].id)

    with db.cursor() as cur:
        cur.execute("SELECT quantidade_disponivel FROM estoque WHERE id = %s", (item_estoque.id,))
        assert cur.fetchone()[0] == 10

        cur.execute("SELECT COUNT(*) FROM pedido_itens")
        assert cur.fetchone()[0] == 0


def test_remover_item_inexistente_nao_levanta_erro(db, repo):
    repo.remover(999999)
