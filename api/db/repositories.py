"""Acesso a dados. Toda consulta de histórico é filtrada pelo usuário dono."""

from .connection import get_connection

# ------------------------------
# Usuários
# ------------------------------


def create_user(email, senha_hash, nome, tamanho_rebanho, tipo_gado):
    """Insere o usuário. Levanta sqlite3.IntegrityError se o e-mail já existir."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO usuarios (email, senha, nome, tamanho_rebanho, tipo_gado) VALUES (?, ?, ?, ?, ?)",
            (email, senha_hash, nome, tamanho_rebanho, tipo_gado),
        )


def get_credentials(email):
    """Retorna (id, senha_hash) ou None."""
    with get_connection() as conn:
        return conn.execute("SELECT id, senha FROM usuarios WHERE email = ?", (email,)).fetchone()


def get_user(usuario_id):
    """Retorna o perfil público do usuário (sem a senha) ou None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, email, nome, tamanho_rebanho, tipo_gado FROM usuarios WHERE id = ?",
            (usuario_id,),
        ).fetchone()
    if not row:
        return None
    keys = ("usuario_id", "email", "nome", "tamanho_rebanho", "tipo_gado")
    return dict(zip(keys, row, strict=True))


# ------------------------------
# Histórico
# ------------------------------


def add_message(usuario_id, conversa_id, pergunta, resposta):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO historico (usuario_id, conversa_id, pergunta, resposta)
            VALUES (?, ?, ?, ?)
        """,
            (usuario_id, conversa_id, pergunta, resposta),
        )


def recent_turns(usuario_id, conversa_id, limit):
    """Últimos `limit` pares (pergunta, resposta) da conversa, do mais antigo ao mais novo."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT pergunta, resposta
            FROM historico
            WHERE usuario_id = ? AND conversa_id = ?
            ORDER BY id DESC
            LIMIT ?
        """,
            (usuario_id, conversa_id, limit),
        ).fetchall()
    return list(reversed(rows))


def list_conversations(usuario_id):
    """Primeira mensagem de cada conversa do usuário, da mais recente para a mais antiga."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT h.conversa_id, h.pergunta, h.resposta, h.data
            FROM historico h
            JOIN (
                SELECT MIN(id) AS primeiro_id
                FROM historico
                WHERE usuario_id = ?
                GROUP BY conversa_id
            ) p ON h.id = p.primeiro_id
            WHERE h.usuario_id = ?
            ORDER BY h.id DESC
        """,
            (usuario_id, usuario_id),
        ).fetchall()


def get_history(usuario_id, conversa_id=None):
    """Mensagens de uma conversa (ou de todas) do usuário, em ordem cronológica."""
    with get_connection() as conn:
        if conversa_id:
            return conn.execute(
                """
                SELECT pergunta, resposta, data
                FROM historico
                WHERE usuario_id = ? AND conversa_id = ?
                ORDER BY id ASC
            """,
                (usuario_id, conversa_id),
            ).fetchall()
        return conn.execute(
            """
            SELECT pergunta, resposta, data
            FROM historico
            WHERE usuario_id = ?
            ORDER BY id ASC
        """,
            (usuario_id,),
        ).fetchall()
