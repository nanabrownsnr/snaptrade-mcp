"""PostgreSQL-backed encrypted credential storage."""

import os

import psycopg
from cryptography.fernet import Fernet

from app.config import settings

_cipher = Fernet(settings.ENCRYPTION_KEY.encode())

def _connect():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required")
    return psycopg.connect(url)

def initialize():
    with _connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS snaptrade_connections (owner_id TEXT PRIMARY KEY, client_id TEXT NOT NULL, consumer_key TEXT NOT NULL, updated_at TIMESTAMPTZ DEFAULT now())")
        conn.commit()

def save_connection(owner_id: str, client_id: str, consumer_key: str) -> None:
    with _connect() as conn:
        conn.execute("INSERT INTO snaptrade_connections(owner_id, client_id, consumer_key) VALUES (%s,%s,%s) ON CONFLICT(owner_id) DO UPDATE SET client_id=EXCLUDED.client_id, consumer_key=EXCLUDED.consumer_key, updated_at=now()", (owner_id, _cipher.encrypt(client_id.encode()).decode(), _cipher.encrypt(consumer_key.encode()).decode()))
        conn.commit()

def get_connection(owner_id: str) -> dict[str, str] | None:
    with _connect() as conn:
        row = conn.execute("SELECT client_id, consumer_key FROM snaptrade_connections WHERE owner_id=%s", (owner_id,)).fetchone()
    if not row:
        return None
    return {"client_id": _cipher.decrypt(row[0].encode()).decode(), "consumer_key": _cipher.decrypt(row[1].encode()).decode()}
