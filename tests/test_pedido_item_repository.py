from decimal import Decimal

import pytest

from app.models.cliente import Cliente
from app.models.estoque import Estoque
from app.models.pedido import Pedido
from app.models.enums import EstadoPedido
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


def test_exibir_um_retorna_item(db, repo, cliente, item_estoque):
    pedido = PedidoRepository().inserir(
        Pedido(cliente_id=cliente.id),
        [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=2)],
    )

    itens = repo.listar_todos()
    item = repo.exibir_um(itens[0].id)

    assert item is not None
    assert item.pedido_id == pedido.id
    assert item.item_id == item_estoque.id
    assert item.quantidade == 2


def test_exibir_um_inexistente_retorna_none(db, repo):
    assert repo.exibir_um(999999) is None


def test_alterar_atualiza_quantidade_e_estoque(db, repo, cliente, item_estoque):
    PedidoRepository().inserir(
        Pedido(cliente_id=cliente.id),
        [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=2)],
    )
    pedido_item = repo.listar_todos()[0]

    atualizado = PedidoItem(
        id=pedido_item.id,
        pedido_id=pedido_item.pedido_id,
        item_id=pedido_item.item_id,
        quantidade=4,
    )

    resultado = repo.alterar(atualizado)

    assert resultado.quantidade == 4

    with db.cursor() as cur:
        cur.execute("SELECT quantidade_disponivel FROM estoque WHERE id = %s", (item_estoque.id,))
        assert cur.fetchone()[0] == 6  # 10 - 4


def test_alterar_reduz_quantidade_restaura_estoque(db, repo, cliente, item_estoque):
    PedidoRepository().inserir(
        Pedido(cliente_id=cliente.id),
        [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=5)],
    )
    pedido_item = repo.listar_todos()[0]

    resultado = repo.alterar(
        PedidoItem(
            id=pedido_item.id,
            pedido_id=pedido_item.pedido_id,
            item_id=pedido_item.item_id,
            quantidade=2,
        )
    )

    assert resultado.quantidade == 2

    with db.cursor() as cur:
        cur.execute("SELECT quantidade_disponivel FROM estoque WHERE id = %s", (item_estoque.id,))
        assert cur.fetchone()[0] == 8  # 10 - 2 (devolveu 3)


def test_alterar_item_inexistente_levanta_erro(db, repo):
    fantasma = PedidoItem(id=999999, pedido_id=1, item_id=1, quantidade=1)

    with pytest.raises(ValueError, match="não encontrado"):
        repo.alterar(fantasma)


def test_alterar_falha_se_estoque_insuficiente(db, repo, cliente, item_estoque):
    PedidoRepository().inserir(
        Pedido(cliente_id=cliente.id),
        [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=9)],
    )
    pedido_item = repo.listar_todos()[0]

    with pytest.raises(ValueError, match="Estoque insuficiente"):
        repo.alterar(
            PedidoItem(
                id=pedido_item.id,
                pedido_id=pedido_item.pedido_id,
                item_id=pedido_item.item_id,
                quantidade=12,
            )
        )


def test_alterar_bloqueia_itens_de_pedido_finalizado(db, repo, cliente, item_estoque):
    pedido_repo = PedidoRepository()
    pedido = pedido_repo.inserir(
        Pedido(cliente_id=cliente.id),
        [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=1)],
    )

    pedido_repo.alterar(
        Pedido(
            id=pedido.id,
            cliente_id=pedido.cliente_id,
            data=pedido.data,
            estado=EstadoPedido.ENTREGUE,
            valor=pedido.valor,
            pago=pedido.pago,
        )
    )

    with pytest.raises(ValueError, match="estado do pedido"):
        repo.alterar(
            PedidoItem(
                id=repo.listar_todos()[0].id,
                pedido_id=pedido.id,
                item_id=item_estoque.id,
                quantidade=2,
            )
        )


def test_alterar_bloqueia_itens_de_cliente_inativo(db, repo, cliente, item_estoque):
    pedido_repo = PedidoRepository()
    pedido_repo.inserir(
        Pedido(cliente_id=cliente.id),
        [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=1)],
    )
    pedido_item = repo.listar_todos()[0]

    with db.cursor() as cur:
        cur.execute("UPDATE clientes SET ativo = FALSE WHERE id = %s", (cliente.id,))
        db.commit()

    with pytest.raises(ValueError, match="cliente inativo"):
        repo.alterar(
            PedidoItem(
                id=pedido_item.id,
                pedido_id=pedido_item.pedido_id,
                item_id=pedido_item.item_id,
                quantidade=2,
            )
        )


def test_alterar_usa_pedido_real_para_validar_estado(db, repo, cliente, item_estoque):
    pedido_repo = PedidoRepository()
    pedido_finalizado = pedido_repo.inserir(
        Pedido(cliente_id=cliente.id),
        [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=1)],
    )
    pedido_repo.alterar(
        Pedido(
            id=pedido_finalizado.id,
            cliente_id=pedido_finalizado.cliente_id,
            data=pedido_finalizado.data,
            estado=EstadoPedido.ENTREGUE,
            valor=pedido_finalizado.valor,
            pago=pedido_finalizado.pago,
        )
    )

    pedido_diferente = pedido_repo.inserir(
        Pedido(cliente_id=cliente.id),
        [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=1)],
    )

    pedido_item = repo.listar_todos()[0]

    with pytest.raises(ValueError, match="estado do pedido"):
        repo.alterar(
            PedidoItem(
                id=pedido_item.id,
                pedido_id=pedido_diferente.id,  # ID errado informado
                item_id=item_estoque.id,
                quantidade=2,
            )
        )


def test_alterar_falha_se_item_estoque_inativo(db, repo, cliente, item_estoque):
    pedido_repo = PedidoRepository()
    pedido_repo.inserir(
        Pedido(cliente_id=cliente.id),
        [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=1)],
    )
    pedido_item = repo.listar_todos()[0]

    EstoqueRepository().remover(item_estoque.id)

    with pytest.raises(ValueError, match="inativo"):
        repo.alterar(
            PedidoItem(
                id=pedido_item.id,
                pedido_id=pedido_item.pedido_id,
                item_id=item_estoque.id,
                quantidade=2,
            )
        )


def test_alterar_recalcula_valor_do_pedido(db, repo, cliente, item_estoque):
    pedido_repo = PedidoRepository()
    pedido = pedido_repo.inserir(
        Pedido(cliente_id=cliente.id),
        [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=1)],
    )

    pedido_item = repo.listar_todos()[0]

    repo.alterar(
        PedidoItem(
            id=pedido_item.id,
            pedido_id=pedido_item.pedido_id,
            item_id=pedido_item.item_id,
            quantidade=3,
        )
    )

    with db.cursor() as cur:
        cur.execute("SELECT valor FROM pedidos WHERE id = %s", (pedido.id,))
        valor_atual = cur.fetchone()[0]

    assert valor_atual == Decimal("45.00")


def test_alterar_falha_se_quantidade_nao_positiva(db, repo, cliente, item_estoque):
    PedidoRepository().inserir(
        Pedido(cliente_id=cliente.id),
        [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=1)],
    )
    pedido_item = repo.listar_todos()[0]

    with pytest.raises(ValueError, match="quantidade"):
        repo.alterar(
            PedidoItem(
                id=pedido_item.id,
                pedido_id=pedido_item.pedido_id,
                item_id=pedido_item.item_id,
                quantidade=0,
            )
        )
