from decimal import Decimal

import pytest

from app.models.estoque import Estoque
from app.repositories.estoque_repository import EstoqueRepository


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
