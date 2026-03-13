from decimal import Decimal

import pytest

from app.models.cliente import Cliente
from app.models.enums import EstadoPedido
from app.models.estoque import Estoque
from app.models.pedido import Pedido
from app.models.pedido_item import PedidoItem
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.estoque_repository import EstoqueRepository
from app.repositories.pedido_repository import PedidoRepository


@pytest.fixture
def repo():
    return PedidoRepository()


@pytest.fixture
def cliente(db):
    return ClienteRepository().inserir(Cliente(nome="Cliente Teste", numero="11900000000"))


@pytest.fixture
def item_estoque(db):
    return EstoqueRepository().inserir(
        Estoque(item="Marmita Frango", quantidade_disponivel=10, valor=Decimal("15.00"))
    )


def test_inserir_retorna_pedido_com_id(db, repo, cliente, item_estoque):
    pedido = Pedido(cliente_id=cliente.id)
    itens = [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=2)]

    resultado = repo.inserir(pedido, itens)

    assert resultado.id is not None
    assert isinstance(resultado.id, int)


def test_inserir_calcula_valor_total(db, repo, cliente, item_estoque):
    pedido = Pedido(cliente_id=cliente.id)
    itens = [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=3)]

    resultado = repo.inserir(pedido, itens)

    assert resultado.valor == Decimal("45.00")  # 3 × R$ 15,00


def test_inserir_com_multiplos_itens(db, repo, cliente, db_dois_itens):
    item_a, item_b = db_dois_itens
    pedido = Pedido(cliente_id=cliente.id)
    itens = [
        PedidoItem(pedido_id=0, item_id=item_a.id, quantidade=1),
        PedidoItem(pedido_id=0, item_id=item_b.id, quantidade=2),
    ]

    resultado = repo.inserir(pedido, itens)

    # item_a: 1 × R$10,00 + item_b: 2 × R$20,00 = R$50,00
    assert resultado.valor == Decimal("50.00")


def test_inserir_atribui_pedido_id_aos_itens(db, repo, cliente, item_estoque):
    pedido = Pedido(cliente_id=cliente.id)
    itens = [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=1)]

    resultado = repo.inserir(pedido, itens)

    assert itens[0].pedido_id == resultado.id
    assert itens[0].id is not None


def test_inserir_decrementa_estoque(db, repo, cliente, item_estoque):
    pedido = Pedido(cliente_id=cliente.id)
    itens = [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=4)]
    repo.inserir(pedido, itens)

    with db.cursor() as cur:
        cur.execute("SELECT quantidade_disponivel FROM estoque WHERE id = %s", (item_estoque.id,))
        qtd = cur.fetchone()[0]

    assert qtd == 6  # 10 - 4


def test_inserir_falha_se_estoque_insuficiente(db, repo, cliente):
    item_limitado = EstoqueRepository().inserir(
        Estoque(item="Item Limitado", quantidade_disponivel=2, valor=Decimal("10.00"))
    )
    pedido = Pedido(cliente_id=cliente.id)
    itens = [PedidoItem(pedido_id=0, item_id=item_limitado.id, quantidade=5)]

    with pytest.raises(ValueError, match="Estoque insuficiente"):
        repo.inserir(pedido, itens)


def test_inserir_falha_se_item_nao_existe(db, repo, cliente):
    pedido = Pedido(cliente_id=cliente.id)
    itens = [PedidoItem(pedido_id=0, item_id=999999, quantidade=1)]

    with pytest.raises(ValueError, match="não encontrado"):
        repo.inserir(pedido, itens)


def test_inserir_itens_duplicados_sao_mesclados_em_uma_linha(db, repo, cliente):
    """Dois PedidoItem com mesmo item_id devem virar uma única linha em pedido_itens."""
    item = EstoqueRepository().inserir(
        Estoque(item="Pastel", quantidade_disponivel=10, valor=Decimal("10.00"))
    )
    pedido = Pedido(cliente_id=cliente.id)
    itens = [
        PedidoItem(pedido_id=0, item_id=item.id, quantidade=3),
        PedidoItem(pedido_id=0, item_id=item.id, quantidade=3),
    ]

    resultado = repo.inserir(pedido, itens)

    with db.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*), SUM(quantidade) FROM pedido_itens WHERE pedido_id = %s",
            (resultado.id,),
        )
        count, total_qtd = cur.fetchone()

    assert count == 1        # uma única linha, não duas
    assert total_qtd == 6    # quantidade somada corretamente
    assert resultado.valor == Decimal("60.00")  # 6 × R$10,00


def test_inserir_falha_se_item_duplicado_excede_estoque(db, repo, cliente):
    """Dois PedidoItem com mesmo item_id somam 6, mas estoque tem 5 — deve falhar."""
    item = EstoqueRepository().inserir(
        Estoque(item="Pastel", quantidade_disponivel=5, valor=Decimal("10.00"))
    )
    pedido = Pedido(cliente_id=cliente.id)
    itens = [
        PedidoItem(pedido_id=0, item_id=item.id, quantidade=3),
        PedidoItem(pedido_id=0, item_id=item.id, quantidade=3),
    ]

    with pytest.raises(ValueError, match="Estoque insuficiente"):
        repo.inserir(pedido, itens)


def test_inserir_aceita_itens_duplicados_dentro_do_estoque(db, repo, cliente):
    """Dois PedidoItem com mesmo item_id somam 4, estoque tem 5 — deve passar."""
    item = EstoqueRepository().inserir(
        Estoque(item="Pastel", quantidade_disponivel=5, valor=Decimal("10.00"))
    )
    pedido = Pedido(cliente_id=cliente.id)
    itens = [
        PedidoItem(pedido_id=0, item_id=item.id, quantidade=2),
        PedidoItem(pedido_id=0, item_id=item.id, quantidade=2),
    ]

    resultado = repo.inserir(pedido, itens)

    assert resultado.id is not None
    assert resultado.valor == Decimal("40.00")  # 4 × R$ 10,00


def test_inserir_falha_se_valor_negativo(db):
    """Gravar um pedido com valor negativo diretamente no banco deve falhar."""
    cliente = ClienteRepository().inserir(Cliente(nome="Teste", numero="11900000000"))
    with db.cursor() as cur:
        with pytest.raises(Exception):
            cur.execute(
                """
                INSERT INTO pedidos (cliente_id, data, estado, valor, pago)
                VALUES (%s, CURRENT_DATE, 'EM_ANDAMENTO', -1.00, false)
                """,
                (cliente.id,),
            )


def test_inserir_falha_se_sem_itens(db, repo, cliente):
    pedido = Pedido(cliente_id=cliente.id)

    with pytest.raises(ValueError, match="pelo menos um item"):
        repo.inserir(pedido, [])


def test_inserir_pedido_cancelado(db, repo, cliente, item_estoque):
    pedido = Pedido(cliente_id=cliente.id, estado=EstadoPedido.CANCELADO)
    itens = [PedidoItem(pedido_id=0, item_id=item_estoque.id, quantidade=1)]

    resultado = repo.inserir(pedido, itens)

    assert resultado.id is not None
    assert resultado.estado == EstadoPedido.CANCELADO


@pytest.fixture
def db_dois_itens(db):
    repo = EstoqueRepository()
    item_a = repo.inserir(Estoque(item="Frango", quantidade_disponivel=10, valor=Decimal("10.00")))
    item_b = repo.inserir(Estoque(item="Carne", quantidade_disponivel=10, valor=Decimal("20.00")))
    return item_a, item_b
