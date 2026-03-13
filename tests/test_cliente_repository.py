import pytest

from app.models.cliente import Cliente
from app.repositories.cliente_repository import ClienteRepository


@pytest.fixture
def repo():
    return ClienteRepository()


def test_inserir_retorna_cliente_com_id(db, repo):
    cliente = Cliente(nome="João Silva", numero="11999990001")
    resultado = repo.inserir(cliente)

    assert resultado.id is not None
    assert isinstance(resultado.id, int)


def test_inserir_preserva_nome_e_numero(db, repo):
    cliente = Cliente(nome="Maria Souza", numero="11888880002")
    resultado = repo.inserir(cliente)

    assert resultado.nome == "Maria Souza"
    assert resultado.numero == "11888880002"


def test_inserir_ids_distintos(db, repo):
    c1 = repo.inserir(Cliente(nome="Ana", numero="11111111111"))
    c2 = repo.inserir(Cliente(nome="Pedro", numero="22222222222"))

    assert c1.id != c2.id


def test_inserir_sem_numero_levanta_erro(db, repo):
    with pytest.raises(Exception):
        repo.inserir(Cliente(nome="Sem Numero", numero=None))


def test_listar_todos_retorna_clientes_inseridos(db, repo):
    repo.inserir(Cliente(nome="Ana", numero="11111111111"))
    repo.inserir(Cliente(nome="Pedro", numero="22222222222"))

    clientes = repo.listar_todos()

    assert len(clientes) == 2
    assert [c.nome for c in clientes] == ["Ana", "Pedro"]
    assert all(isinstance(c.id, int) for c in clientes)


def test_remover_remove_cliente_por_id(db, repo):
    cliente = repo.inserir(Cliente(nome="Remover", numero="11333333333"))

    repo.remover(cliente.id)

    clientes = repo.listar_todos()
    assert clientes == []


def test_remover_cliente_inexistente_nao_levanta_erro(db, repo):
    repo.remover(999999)
