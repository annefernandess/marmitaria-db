from app.database import get_connection
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.repositories.cliente_repository import ClienteRepository


class UsuarioRepository:
    def cadastrar(self, usuario: Usuario) -> Usuario:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM usuarios WHERE email = %s AND ativo = TRUE LIMIT 1",
                    (usuario.email,),
                )
                if cur.fetchone() is not None:
                    raise ValueError("Já existe um usuário ativo com este email.")

                cliente_id = usuario.cliente_id
                if usuario.role == "user" and cliente_id is None:
                    cliente = ClienteRepository().inserir(
                        Cliente(nome=usuario.nome, numero=usuario.numero)
                    )
                    cliente_id = cliente.id

                cur.execute(
                    """
                    INSERT INTO usuarios (nome, email, senha, numero, role, cliente_id, ativo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        usuario.nome,
                        usuario.email,
                        usuario.senha,
                        usuario.numero,
                        usuario.role,
                        cliente_id,
                        usuario.ativo,
                    ),
                )
                usuario.id = cur.fetchone()[0]
                usuario.cliente_id = cliente_id
            conn.commit()
        return usuario

    def autenticar(self, email: str, senha: str) -> Usuario:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, nome, email, senha, numero, role, cliente_id, ativo
                    FROM usuarios
                    WHERE email = %s AND ativo = TRUE
                    """,
                    (email,),
                )
                row = cur.fetchone()

        if row is None or row[3] != senha:
            raise ValueError("E-mail ou senha inválidos.")

        return Usuario(
            id=row[0],
            nome=row[1],
            email=row[2],
            senha=row[3],
            numero=row[4],
            role=row[5],
            cliente_id=row[6],
            ativo=row[7],
        )
