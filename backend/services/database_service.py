import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
configured_database_path = os.getenv("DATABASE_PATH", "").strip()

# Use PostgreSQL if DATABASE_URL is provided, otherwise SQLite
if DATABASE_URL:
    # PostgreSQL configuration
    USE_POSTGRESQL = True
    DATABASE_PATH = None
else:
    # SQLite configuration (fallback)
    USE_POSTGRESQL = False
    DATABASE_PATH = (
        Path(configured_database_path)
        if configured_database_path
        else BASE_DIR / "data" / "enterprise.db"
    )

# PostgreSQL connection
def get_postgres_connection():
    """Get PostgreSQL connection if configured."""
    if not USE_POSTGRESQL:
        raise RuntimeError("PostgreSQL not configured. Set DATABASE_URL environment variable.")
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = RealDictCursor
        return conn
    except ImportError:
        raise RuntimeError("psycopg2-binary not installed. Install with: pip install psycopg2-binary")
    except Exception as e:
        raise RuntimeError(f"Failed to connect to PostgreSQL: {str(e)}")

# SQLite connection (fallback)
def get_sqlite_connection():
    """Get SQLite connection."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    
    return connection

# Main connection function
def get_connection():
    """Get database connection based on configuration."""
    if USE_POSTGRESQL:
        return get_postgres_connection()
    else:
        return get_sqlite_connection()


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def init_database():
    """Initialize database schema for both SQLite and PostgreSQL."""
    if USE_POSTGRESQL:
        init_postgresql_database()
    else:
        init_sqlite_database()

def init_sqlite_database():
    """Initialize SQLite database schema."""
    with get_sqlite_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(conversations)"
            ).fetchall()
        }

        if "user_id" not in columns:
            connection.execute(
                "ALTER TABLE conversations ADD COLUMN user_id INTEGER"
            )

        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

def init_postgresql_database():
    """Initialize PostgreSQL database schema."""
    try:
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                session_id VARCHAR(100) PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add user_id column if not exists (for migration)
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'conversations' AND column_name = 'user_id'
                ) THEN
                    ALTER TABLE conversations ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
                END IF;
            END $$;
        """)
        
        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(100) NOT NULL REFERENCES conversations(session_id) ON DELETE CASCADE,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        raise RuntimeError(f"Failed to initialize PostgreSQL database: {str(e)}")


def create_user(username: str, password_hash: str):
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        if USE_POSTGRESQL:
            conn = get_postgres_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, created_at)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (username, password_hash, timestamp),
            )
            
            result = cursor.fetchone()
            user_id = result['id']
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                "id": user_id,
                "username": username,
            }
        else:
            with get_sqlite_connection() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO users (username, password_hash, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (username, password_hash, timestamp),
                )

                return {
                    "id": cursor.lastrowid,
                    "username": username,
                }

    except sqlite3.IntegrityError:
        raise ValueError("That username is already registered.")
    except Exception as e:
        if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
            raise ValueError("That username is already registered.")
        raise RuntimeError(f"Failed to create user: {str(e)}")


def get_user_by_username(username: str):
    if USE_POSTGRESQL:
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, username, password_hash
            FROM users
            WHERE username = %s
            """,
            (username,),
        )
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return dict(row) if row else None
    else:
        with get_sqlite_connection() as connection:
            row = connection.execute(
                """
                SELECT id, username, password_hash
                FROM users
                WHERE username = ?
                """,
                (username,),
            ).fetchone()

        return dict(row) if row else None


def get_user_by_id(user_id: int):
    if USE_POSTGRESQL:
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, username
            FROM users
            WHERE id = %s
            """,
            (user_id,),
        )
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return dict(row) if row else None
    else:
        with get_sqlite_connection() as connection:
            row = connection.execute(
                """
                SELECT id, username
                FROM users
                WHERE id = ?
                """,
                (user_id,),
            ).fetchone()

        return dict(row) if row else None


def verify_conversation_owner(user_id: int, session_id: str):
    if USE_POSTGRESQL:
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT user_id
            FROM conversations
            WHERE session_id = %s
            """,
            (session_id,),
        )
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
    else:
        with get_sqlite_connection() as connection:
            row = connection.execute(
                """
                SELECT user_id
                FROM conversations
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()

    if row and row["user_id"] != user_id:
        raise PermissionError(
            "You do not have access to this conversation."
        )


def save_turn(
    user_id: int,
    session_id: str,
    question: str,
    answer: str,
):
    verify_conversation_owner(user_id, session_id)

    timestamp = datetime.now(timezone.utc).isoformat()

    if USE_POSTGRESQL:
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        # Insert conversation if not exists
        cursor.execute(
            """
            INSERT INTO conversations (session_id, user_id, created_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (session_id) DO NOTHING
            """,
            (session_id, user_id, timestamp),
        )
        
        # Insert messages
        cursor.execute(
            """
            INSERT INTO messages (session_id, role, content, created_at)
            VALUES (%s, %s, %s, %s)
            """,
            (session_id, "user", question, timestamp),
        )
        
        cursor.execute(
            """
            INSERT INTO messages (session_id, role, content, created_at)
            VALUES (%s, %s, %s, %s)
            """,
            (session_id, "assistant", answer, timestamp),
        )
        
        conn.commit()
        cursor.close()
        conn.close()
    else:
        with get_sqlite_connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO conversations
                (session_id, user_id, created_at)
                VALUES (?, ?, ?)
                """,
                (session_id, user_id, timestamp),
            )

            connection.executemany(
                """
                INSERT INTO messages
                (session_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (session_id, "user", question, timestamp),
                    (session_id, "assistant", answer, timestamp),
                ],
            )


def get_history(user_id: int, session_id: str):
    verify_conversation_owner(user_id, session_id)

    if USE_POSTGRESQL:
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT role, content
            FROM messages
            WHERE session_id = %s
            ORDER BY id DESC
            LIMIT 12
            """,
            (session_id,),
        )
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
    else:
        with get_sqlite_connection() as connection:
            rows = connection.execute(
                """
                SELECT role, content
                FROM messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT 12
                """,
                (session_id,),
            ).fetchall()

    if not rows:
        return "No previous conversation."

    return "\n".join(
        f"{row['role'].title()}: {row['content']}"
        for row in reversed(rows)
    )


def get_messages(user_id: int, session_id: str):
    verify_conversation_owner(user_id, session_id)

    if USE_POSTGRESQL:
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, role, content, created_at
            FROM messages
            WHERE session_id = %s
            ORDER BY id
            """,
            (session_id,),
        )
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
    else:
        with get_sqlite_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, role, content, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY id
                """,
                (session_id,),
            ).fetchall()

    return [dict(row) for row in rows]


def delete_conversation(user_id: int, session_id: str):
    verify_conversation_owner(user_id, session_id)

    if USE_POSTGRESQL:
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM messages WHERE session_id = %s",
            (session_id,),
        )

        cursor.execute(
            "DELETE FROM conversations WHERE session_id = %s",
            (session_id,),
        )
        
        conn.commit()
        cursor.close()
        conn.close()
    else:
        with get_sqlite_connection() as connection:
            connection.execute(
                "DELETE FROM messages WHERE session_id = ?",
                (session_id,),
            )

            connection.execute(
                "DELETE FROM conversations WHERE session_id = ?",
                (session_id,),
            )