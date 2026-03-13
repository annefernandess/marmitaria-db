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
