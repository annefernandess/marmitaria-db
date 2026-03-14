from decimal import Decimal

import pytest

from app.models.cliente import Cliente
from app.models.estoque import Estoque
from app.models.pedido import Pedido
from app.models.pedido_item import PedidoItem
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.estoque_repository import EstoqueRepository
from app.repositories.pedido_repository import PedidoRepository


@pytest.fixture
def repo():
    return EstoqueRepository()


def test_inserir_retorna_estoque_com_id(db, repo):
    item = Estoque(item="Marmita Frango", quantidade_disponivel=10, valor=Decimal("15.90"))
    resultado = repo.inserir(item)

    assert resultado.id is not None
    assert isinstance(resultado.id, int)


def test_inserir_preserva_campos(db, repo):
    item = Estoque(item="Marmita Carne", quantidade_disponivel=5, valor=Decimal("18.50"))
    resultado = repo.inserir(item)

    assert resultado.item == "Marmita Carne"
    assert resultado.quantidade_disponivel == 5
    assert resultado.valor == Decimal("18.50")


def test_inserir_ids_distintos(db, repo):
    i1 = repo.inserir(Estoque(item="Frango", quantidade_disponivel=10, valor=Decimal("15.00")))
    i2 = repo.inserir(Estoque(item="Carne", quantidade_disponivel=8, valor=Decimal("17.00")))

    assert i1.id != i2.id


def test_inserir_valor_zero_levanta_erro(db, repo):
    with pytest.raises(Exception):
        repo.inserir(Estoque(item="Item Invalido", quantidade_disponivel=5, valor=Decimal("0")))


def test_inserir_quantidade_negativa_levanta_erro(db, repo):
    with pytest.raises(Exception):
        repo.inserir(Estoque(item="Item Invalido", quantidade_disponivel=-1, valor=Decimal("10.00")))


def test_listar_todos_retorna_itens_inseridos(db, repo):
    repo.inserir(Estoque(item="Frango", quantidade_disponivel=10, valor=Decimal("15.00")))
    repo.inserir(Estoque(item="Carne", quantidade_disponivel=8, valor=Decimal("17.00")))

    itens = repo.listar_todos()

    assert len(itens) == 2
    assert [i.item for i in itens] == ["Frango", "Carne"]
    assert all(isinstance(i.id, int) for i in itens)


def test_remover_remove_item_por_id(db, repo):
    item = repo.inserir(Estoque(item="Remover", quantidade_disponivel=1, valor=Decimal("10.00")))

    repo.remover(item.id)

    itens = repo.listar_todos()
    assert itens == []


def test_remover_item_inexistente_nao_levanta_erro(db, repo):
    repo.remover(999999)


def test_listar_todos_ignora_itens_inativos(db, repo):
    ativo = repo.inserir(Estoque(item="Ativo", quantidade_disponivel=5, valor=Decimal("12.00")))
    inativo = repo.inserir(Estoque(item="Inativo", quantidade_disponivel=3, valor=Decimal("9.00")))

    # Remoção lógica do item "Inativo"
    repo.remover(inativo.id)

    itens = repo.listar_todos()

    nomes = [i.item for i in itens]
    assert "Ativo" in nomes
    assert "Inativo" not in nomes


def test_inserir_pedido_falha_se_item_inativo(db):
    cliente = ClienteRepository().inserir(Cliente(nome="Cliente", numero="11900000000"))
    estoque_repo = EstoqueRepository()
    pedido_repo = PedidoRepository()

    item = estoque_repo.inserir(Estoque(item="Marmita", quantidade_disponivel=5, valor=Decimal("10.00")))
    estoque_repo.remover(item.id)  # soft delete (ativo = FALSE)

    with pytest.raises(ValueError, match="inativo"):
        pedido_repo.inserir(
            Pedido(cliente_id=cliente.id),
            [PedidoItem(pedido_id=0, item_id=item.id, quantidade=1)],
        )


def test_alterar_atualiza_campos(db, repo):
    item = repo.inserir(Estoque(item="Marmita", quantidade_disponivel=5, valor=Decimal("10.00")))

    atualizado = Estoque(
        id=item.id,
        item="Marmita Fit",
        quantidade_disponivel=8,
        valor=Decimal("12.50"),
    )

    resultado = repo.alterar(atualizado)

    assert resultado.id == item.id
    assert resultado.item == "Marmita Fit"
    assert resultado.quantidade_disponivel == 8
    assert resultado.valor == Decimal("12.50")

    with db.cursor() as cur:
        cur.execute(
            "SELECT item, quantidade_disponivel, valor FROM estoque WHERE id = %s",
            (item.id,),
        )
        row = cur.fetchone()

    assert row == ("Marmita Fit", 8, Decimal("12.50"))


def test_alterar_item_inexistente_levanta_erro(db, repo):
    inexistente = Estoque(id=999999, item="Ghost", quantidade_disponivel=1, valor=Decimal("1.00"))

    with pytest.raises(ValueError, match="não encontrado"):
        repo.alterar(inexistente)


def test_alterar_item_inativo_levanta_erro(db, repo):
    item = repo.inserir(Estoque(item="Marmita", quantidade_disponivel=5, valor=Decimal("10.00")))
    repo.remover(item.id)

    with pytest.raises(ValueError, match="inativo"):
        repo.alterar(
            Estoque(
                id=item.id,
                item="Marmita Nova",
                quantidade_disponivel=3,
                valor=Decimal("9.00"),
            )
        )


def test_buscar_por_nome_parcial_case_insensitive(db, repo):
    frango = repo.inserir(Estoque(item="Marmita Frango", quantidade_disponivel=5, valor=Decimal("10.00")))
    grelhado = repo.inserir(
        Estoque(item="Frango Grelhado", quantidade_disponivel=4, valor=Decimal("12.00"))
    )
    repo.inserir(Estoque(item="Carne", quantidade_disponivel=3, valor=Decimal("15.00")))

    resultados = repo.buscar_por_nome("frango")

    assert [r.id for r in resultados] == [frango.id, grelhado.id]


def test_buscar_por_nome_ignora_inativos(db, repo):
    ativo = repo.inserir(Estoque(item="Vegano", quantidade_disponivel=2, valor=Decimal("11.00")))
    inativo = repo.inserir(Estoque(item="Vegano Especial", quantidade_disponivel=1, valor=Decimal("13.00")))
    repo.remover(inativo.id)

    resultados = repo.buscar_por_nome("vega")

    assert [r.id for r in resultados] == [ativo.id]


def test_exibir_um_retorna_item_ativo(db, repo):
    item = repo.inserir(Estoque(item="Sobremesa", quantidade_disponivel=6, valor=Decimal("8.00")))

    resultado = repo.exibir_um(item.id)

    assert resultado is not None
    assert resultado.id == item.id
    assert resultado.item == "Sobremesa"


def test_exibir_um_inativo_ou_inexistente_retorna_none(db, repo):
    item = repo.inserir(Estoque(item="Suco", quantidade_disponivel=10, valor=Decimal("5.00")))
    repo.remover(item.id)

    assert repo.exibir_um(item.id) is None
    assert repo.exibir_um(999999) is None
