from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content_html TEXT NOT NULL DEFAULT '',
    source_filename TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS document_shares (
    document_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (document_id, user_id),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""


SEEDED_USERS = (
    ("Mahipal Baithi", "mahipal.baithi05@gmail.com"),
    ("Ava Sharma", "ava@ajaia.local"),
    ("Noah Patel", "noah@ajaia.local"),
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_database(database_path: str | Path) -> None:
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(database_path)) as connection:
        connection.executescript(SCHEMA)
        for name, email in SEEDED_USERS:
            connection.execute(
                """
                INSERT INTO users (name, email)
                VALUES (?, ?)
                ON CONFLICT(email) DO UPDATE SET name = excluded.name
                """,
                (name, email),
            )
        connection.commit()


def fetch_users(database_path: str | Path) -> list[sqlite3.Row]:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            "SELECT id, name, email FROM users ORDER BY name"
        ).fetchall()


def get_user(database_path: str | Path, user_id: int) -> sqlite3.Row | None:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            "SELECT id, name, email FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()


def create_document(
    database_path: str | Path,
    owner_id: int,
    title: str,
    content_html: str = "",
    source_filename: str | None = None,
) -> int:
    timestamp = utc_now()
    with closing(connect(database_path)) as connection:
        cursor = connection.execute(
            """
            INSERT INTO documents (owner_id, title, content_html, source_filename, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (owner_id, title, content_html, source_filename, timestamp, timestamp),
        )
        connection.commit()
        return int(cursor.lastrowid)


def get_document(
    database_path: str | Path,
    document_id: int,
    viewer_id: int | None = None,
) -> sqlite3.Row | None:
    with closing(connect(database_path)) as connection:
        document = connection.execute(
            """
            SELECT
                d.id,
                d.owner_id,
                d.title,
                d.content_html,
                d.source_filename,
                d.created_at,
                d.updated_at,
                owner.name AS owner_name,
                owner.email AS owner_email
            FROM documents d
            JOIN users owner ON owner.id = d.owner_id
            WHERE d.id = ?
            """,
            (document_id,),
        ).fetchone()

        if document is None:
            return None

        if viewer_id is None:
            return document

        if document["owner_id"] == viewer_id:
            return document

        shared = connection.execute(
            """
            SELECT 1
            FROM document_shares
            WHERE document_id = ? AND user_id = ?
            """,
            (document_id, viewer_id),
        ).fetchone()
        return document if shared else None


def update_document(
    database_path: str | Path,
    document_id: int,
    user_id: int,
    title: str,
    content_html: str,
) -> sqlite3.Row | None:
    if get_document(database_path, document_id, user_id) is None:
        return None

    timestamp = utc_now()
    with closing(connect(database_path)) as connection:
        connection.execute(
            """
            UPDATE documents
            SET title = ?, content_html = ?, updated_at = ?
            WHERE id = ?
            """,
            (title, content_html, timestamp, document_id),
        )
        connection.commit()

    return get_document(database_path, document_id, user_id)


def get_dashboard_documents(
    database_path: str | Path, user_id: int
) -> tuple[list[sqlite3.Row], list[sqlite3.Row]]:
    with closing(connect(database_path)) as connection:
        owned = connection.execute(
            """
            SELECT
                d.id,
                d.title,
                d.content_html,
                d.source_filename,
                d.created_at,
                d.updated_at,
                COUNT(ds.user_id) AS share_count
            FROM documents d
            LEFT JOIN document_shares ds ON ds.document_id = d.id
            WHERE d.owner_id = ?
            GROUP BY d.id
            ORDER BY d.updated_at DESC
            """,
            (user_id,),
        ).fetchall()

        shared = connection.execute(
            """
            SELECT
                d.id,
                d.title,
                d.content_html,
                d.source_filename,
                d.created_at,
                d.updated_at,
                owner.name AS owner_name,
                owner.email AS owner_email
            FROM document_shares ds
            JOIN documents d ON d.id = ds.document_id
            JOIN users owner ON owner.id = d.owner_id
            WHERE ds.user_id = ?
            ORDER BY d.updated_at DESC
            """,
            (user_id,),
        ).fetchall()

    return owned, shared


def get_shared_users(database_path: str | Path, document_id: int) -> list[sqlite3.Row]:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            """
            SELECT u.id, u.name, u.email
            FROM document_shares ds
            JOIN users u ON u.id = ds.user_id
            WHERE ds.document_id = ?
            ORDER BY u.name
            """,
            (document_id,),
        ).fetchall()


def get_share_candidates(
    database_path: str | Path, document_id: int, owner_id: int
) -> list[sqlite3.Row]:
    with closing(connect(database_path)) as connection:
        return connection.execute(
            """
            SELECT id, name, email
            FROM users
            WHERE id != ?
            AND id NOT IN (
                SELECT user_id
                FROM document_shares
                WHERE document_id = ?
            )
            ORDER BY name
            """,
            (owner_id, document_id),
        ).fetchall()


def add_share(
    database_path: str | Path,
    document_id: int,
    owner_id: int,
    target_user_id: int,
) -> bool:
    document = get_document(database_path, document_id)
    if document is None or document["owner_id"] != owner_id or target_user_id == owner_id:
        return False

    with closing(connect(database_path)) as connection:
        existing_target = connection.execute(
            "SELECT 1 FROM users WHERE id = ?",
            (target_user_id,),
        ).fetchone()
        if existing_target is None:
            return False

        connection.execute(
            """
            INSERT OR IGNORE INTO document_shares (document_id, user_id, created_at)
            VALUES (?, ?, ?)
            """,
            (document_id, target_user_id, utc_now()),
        )
        connection.commit()
    return True
