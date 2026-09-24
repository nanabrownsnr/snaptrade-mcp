"""Encrypted credential storage with an in-memory fallback for local development."""

from cryptography.fernet import Fernet

from app.config import settings

_cipher = Fernet(settings.ENCRYPTION_KEY)
_records: dict[str, dict[str, str]] = {}


def save_connection(owner_id: str, client_id: str, consumer_key: str) -> None:
    _records[owner_id] = {
        "client_id": _cipher.encrypt(client_id.encode()).decode(),
        "consumer_key": _cipher.encrypt(consumer_key.encode()).decode(),
    }


def get_connection(owner_id: str) -> dict[str, str] | None:
    record = _records.get(owner_id)
    if record is None:
        return None
    return {key: _cipher.decrypt(value.encode()).decode() for key, value in record.items()}
