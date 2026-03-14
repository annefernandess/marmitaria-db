import pytest
from decimal import Decimal

from app.models.cliente import Cliente
from app.models.estoque import Estoque
from app.models.pedido import Pedido
from app.models.pedido_item import PedidoItem
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.estoque_repository import EstoqueRepository
from app.repositories.pedido_repository import PedidoRepository


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

    with db.cursor() as cur:
        cur.execute("SELECT ativo FROM clientes WHERE id = %s", (cliente.id,))
        assert cur.fetchone()[0] is False


def test_remover_cliente_inexistente_nao_levanta_erro(db, repo):
    repo.remover(999999)


def test_remover_cliente_com_pedidos_levanta_erro_e_preserva_historico(db, repo):
    cliente = repo.inserir(Cliente(nome="Cliente com Pedido", numero="11444444444"))
    item = EstoqueRepository().inserir(
        Estoque(item="Marmita", quantidade_disponivel=10, valor=Decimal("10.00"))
    )

    pedido = PedidoRepository().inserir(
        Pedido(cliente_id=cliente.id),
        [PedidoItem(pedido_id=0, item_id=item.id, quantidade=1)],
    )
    with pytest.raises(Exception):
        repo.remover(cliente.id)

    with db.cursor() as cur:
        cur.execute("SELECT ativo FROM clientes WHERE id = %s", (cliente.id,))
        assert cur.fetchone()[0] is True

        cur.execute("SELECT COUNT(*) FROM pedidos WHERE id = %s", (pedido.id,))
        assert cur.fetchone()[0] == 1


def test_alterar_atualiza_nome_e_numero(db, repo):
    cliente = repo.inserir(Cliente(nome="Original", numero="11000000000"))

    atualizado = Cliente(id=cliente.id, nome="Atualizado", numero="11999999999")
    resultado = repo.alterar(atualizado)

    assert resultado.id == cliente.id
    assert resultado.nome == "Atualizado"
    assert resultado.numero == "11999999999"

    with db.cursor() as cur:
        cur.execute("SELECT nome, numero FROM clientes WHERE id = %s", (cliente.id,))
        assert cur.fetchone() == ("Atualizado", "11999999999")


def test_alterar_cliente_inexistente_levanta_erro(db, repo):
    fantasma = Cliente(id=999999, nome="Ghost", numero="11000000000")

    with pytest.raises(ValueError, match="não encontrado"):
        repo.alterar(fantasma)


def test_alterar_cliente_inativo_levanta_erro(db, repo):
    cliente = repo.inserir(Cliente(nome="Para Inativar", numero="11777777777"))
    repo.remover(cliente.id)

    with pytest.raises(ValueError, match="inativo"):
        repo.alterar(Cliente(id=cliente.id, nome="Novo", numero="11988888888"))


def test_alterar_numero_duplicado_levanta_erro(db, repo):
    existente = repo.inserir(Cliente(nome="Existente", numero="11111111111"))
    outro = repo.inserir(Cliente(nome="Outro", numero="22222222222"))

    with pytest.raises(ValueError, match="já cadastrado"):
        repo.alterar(Cliente(id=outro.id, nome="Outro", numero="11111111111"))


def test_buscar_por_nome_parcial_case_insensitive(db, repo):
    ana = repo.inserir(Cliente(nome="Ana Paula", numero="11111111111"))
    joana = repo.inserir(Cliente(nome="Joana", numero="12222222222"))
    repo.inserir(Cliente(nome="Pedro", numero="13333333333"))

    resultados = repo.buscar_por_nome("ana")

    assert [r.id for r in resultados] == [ana.id, joana.id]


def test_buscar_por_nome_ignora_inativos(db, repo):
    ativo = repo.inserir(Cliente(nome="Carlos", numero="14444444444"))
    inativo = repo.inserir(Cliente(nome="Carlos Eduardo", numero="15555555555"))
    repo.remover(inativo.id)

    resultados = repo.buscar_por_nome("carlos")

    assert [r.id for r in resultados] == [ativo.id]


def test_exibir_um_retorna_cliente_ativo(db, repo):
    cliente = repo.inserir(Cliente(nome="Bianca", numero="16666666666"))

    resultado = repo.exibir_um(cliente.id)

    assert resultado is not None
    assert resultado.id == cliente.id
    assert resultado.nome == "Bianca"


def test_exibir_um_inativo_ou_inexistente_retorna_none(db, repo):
    cliente = repo.inserir(Cliente(nome="Inativar", numero="17777777777"))
    repo.remover(cliente.id)

    assert repo.exibir_um(cliente.id) is None
    assert repo.exibir_um(999999) is None
