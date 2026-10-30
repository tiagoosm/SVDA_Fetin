"""Data access. Every message query is scoped to the owning user."""

from .connection import get_connection

# ------------------------------
# Users
# ------------------------------


def create_user(email, password_hash, name, herd_size, cattle_type):
    """Insert a user. Raises sqlite3.IntegrityError if the e-mail already exists."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (email, password_hash, name, herd_size, cattle_type) VALUES (?, ?, ?, ?, ?)",
            (email, password_hash, name, herd_size, cattle_type),
        )


def get_credentials(email):
    """Return (id, password_hash) or None."""
    with get_connection() as conn:
        return conn.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,)).fetchone()


def get_user(user_id):
    """Return the public profile (never the password hash) or None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, email, name, herd_size, cattle_type FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if not row:
        return None
    return dict(zip(("id", "email", "name", "herd_size", "cattle_type"), row, strict=True))


# ------------------------------
# Messages
# ------------------------------


def add_message(user_id, conversation_id, question, answer):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO messages (user_id, conversation_id, question, answer) VALUES (?, ?, ?, ?)",
            (user_id, conversation_id, question, answer),
        )


def recent_turns(user_id, conversation_id, limit):
    """The last `limit` (question, answer) pairs of the conversation, oldest first."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT question, answer
            FROM messages
            WHERE user_id = ? AND conversation_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, conversation_id, limit),
        ).fetchall()
    return list(reversed(rows))


def count_messages_since(since):
    """Messages saved by all users since `since` ('YYYY-MM-DD HH:MM:SS', UTC)."""
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM messages WHERE created_at >= ?", (since,)).fetchone()[0]


def list_conversations(user_id):
    """First message of each of the user's conversations, most recent first."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT m.conversation_id, m.question, m.answer, m.created_at
            FROM messages m
            JOIN (
                SELECT MIN(id) AS first_id
                FROM messages
                WHERE user_id = ?
                GROUP BY conversation_id
            ) f ON m.id = f.first_id
            WHERE m.user_id = ?
            ORDER BY m.id DESC
            """,
            (user_id, user_id),
        ).fetchall()


def get_conversation_messages(user_id, conversation_id):
    """(question, answer, created_at) rows of one conversation, in chronological order."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT question, answer, created_at
            FROM messages
            WHERE user_id = ? AND conversation_id = ?
            ORDER BY id ASC
            """,
            (user_id, conversation_id),
        ).fetchall()
