from app.database import get_connection
from app.models.cliente import Cliente


class ClienteRepository:
    def inserir(self, cliente: Cliente) -> Cliente:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO clientes (nome, numero, ativo)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (cliente.nome, cliente.numero, cliente.ativo),
                )
                cliente.id = cur.fetchone()[0]
            conn.commit()
        return cliente

    def listar_todos(self) -> list[Cliente]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, nome, numero, ativo
                    FROM clientes
                    WHERE ativo = TRUE
                    ORDER BY id
                    """
                )
                rows = cur.fetchall()

        return [Cliente(id=row[0], nome=row[1], numero=row[2], ativo=row[3]) for row in rows]

    def exibir_um(self, cliente_id: int) -> Cliente | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, nome, numero, ativo
                    FROM clientes
                    WHERE id = %s
                    """,
                    (cliente_id,),
                )
                row = cur.fetchone()

        if row is None or row[3] is not True:
            return None

        return Cliente(id=row[0], nome=row[1], numero=row[2], ativo=row[3])

    def buscar_por_nome(self, termo: str) -> list[Cliente]:
        like = f"%{termo}%"
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, nome, numero, ativo
                    FROM clientes
                    WHERE ativo = TRUE AND nome ILIKE %s
                    ORDER BY id
                    """,
                    (like,),
                )
                rows = cur.fetchall()

        return [Cliente(id=row[0], nome=row[1], numero=row[2], ativo=row[3]) for row in rows]

    def alterar(self, cliente: Cliente) -> Cliente:
        if cliente.id is None:
            raise ValueError("ID do cliente é obrigatório para alterar.")

        with get_connection() as conn:
            with conn.cursor() as cur:
                # Verifica se o cliente existe e está ativo antes de checar duplicidade
                cur.execute(
                    "SELECT ativo FROM clientes WHERE id = %s",
                    (cliente.id,),
                )
                row = cur.fetchone()

                if row is None or row[0] is not True:
                    raise ValueError("Cliente não encontrado ou inativo.")

                # Verifica se já existe outro cliente ativo com o mesmo número
                cur.execute(
                    """
                    SELECT 1
                    FROM clientes
                    WHERE numero = %s AND id <> %s AND ativo = TRUE
                    LIMIT 1
                    """,
                    (cliente.numero, cliente.id),
                )
                duplicado = cur.fetchone() is not None

                if duplicado:
                    raise ValueError("Número já cadastrado para outro cliente ativo.")

                cur.execute(
                    """
                    UPDATE clientes
                    SET nome = %s, numero = %s
                    WHERE id = %s AND ativo = TRUE
                    RETURNING id
                    """,
                    (cliente.nome, cliente.numero, cliente.id),
                )
                updated = cur.fetchone()
            conn.commit()

        if updated is None:
            raise ValueError("Cliente não encontrado ou inativo.")

        return cliente

    def remover(self, cliente_id: int) -> None:
        has_pedidos = False
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pedidos WHERE cliente_id = %s LIMIT 1",
                    (cliente_id,),
                )
                has_pedidos = cur.fetchone() is not None

                if not has_pedidos:
                    cur.execute(
                        "UPDATE clientes SET ativo = FALSE WHERE id = %s",
                        (cliente_id,),
                    )
            conn.commit()

        if has_pedidos:
            raise ValueError("Não é possível remover: cliente possui pedidos vinculados.")
