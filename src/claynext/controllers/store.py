"""SQLite key pool for the LLM lab (no Studio GUI store).

Mirrors the ApiKey methods that ``llm_keys.ApiKeyPool`` needs. Secrets stay in
``data/lab.db`` under this project or in environment variables. Do not commit
the database.
"""
from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from claynext.utils.paths import DATA_DIR, ensure_data_dirs

_LOCK = threading.Lock()
_STORE: "LabStore | None" = None


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class LabStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        return con

    def _init_schema(self) -> None:
        with self._connect() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    secret TEXT NOT NULL,
                    label TEXT NOT NULL DEFAULT '',
                    enabled INTEGER NOT NULL DEFAULT 1,
                    fail_count INTEGER NOT NULL DEFAULT 0,
                    cooldown_until TEXT,
                    last_used_at TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS llm_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    model TEXT,
                    ok INTEGER NOT NULL,
                    latency_ms REAL,
                    error TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )

    def migrate_legacy_api_keys(self) -> None:
        return None

    def list_api_keys(self, provider: str | None = None) -> list[dict[str, Any]]:
        with self._connect() as con:
            if provider:
                rows = con.execute(
                    "SELECT * FROM api_keys WHERE provider = ? ORDER BY id",
                    (provider,),
                ).fetchall()
            else:
                rows = con.execute("SELECT * FROM api_keys ORDER BY id").fetchall()
        return [dict(row) for row in rows]

    def add_api_key(self, provider: str, secret: str, label: str = "") -> dict[str, Any]:
        with self._connect() as con:
            cur = con.execute(
                "INSERT INTO api_keys (provider, secret, label, enabled, created_at) VALUES (?, ?, ?, 1, ?)",
                (provider, secret, label or "", _now()),
            )
            key_id = int(cur.lastrowid)
            row = con.execute("SELECT * FROM api_keys WHERE id = ?", (key_id,)).fetchone()
        return dict(row)

    def delete_api_key(self, key_id: int) -> None:
        with self._connect() as con:
            con.execute("DELETE FROM api_keys WHERE id = ?", (int(key_id),))

    def set_api_key_enabled(self, key_id: int, enabled: bool) -> None:
        with self._connect() as con:
            con.execute(
                "UPDATE api_keys SET enabled = ? WHERE id = ?",
                (1 if enabled else 0, int(key_id)),
            )

    def update_api_key(self, key_id: int, **fields: Any) -> None:
        allowed = {"label", "secret", "enabled"}
        sets = []
        values: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            if key == "enabled":
                value = 1 if value else 0
            sets.append(f"{key} = ?")
            values.append(value)
        if not sets:
            return
        values.append(int(key_id))
        with self._connect() as con:
            con.execute(f"UPDATE api_keys SET {', '.join(sets)} WHERE id = ?", values)

    def update_api_key_state(
        self,
        key_id: int,
        *,
        last_used_at: str | None = None,
        fail_count: int | None = None,
        cooldown_until: str | None = None,
        clear_cooldown: bool = False,
    ) -> None:
        sets: list[str] = []
        values: list[Any] = []
        if last_used_at is not None:
            sets.append("last_used_at = ?")
            values.append(last_used_at)
        if fail_count is not None:
            sets.append("fail_count = ?")
            values.append(int(fail_count))
        if clear_cooldown:
            sets.append("cooldown_until = NULL")
        elif cooldown_until is not None:
            sets.append("cooldown_until = ?")
            values.append(cooldown_until)
        if not sets:
            return
        values.append(int(key_id))
        with self._connect() as con:
            con.execute(f"UPDATE api_keys SET {', '.join(sets)} WHERE id = ?", values)

    def llm_usage(self, provider: str) -> dict[str, Any]:
        with self._connect() as con:
            row = con.execute(
                "SELECT COUNT(*) AS n, AVG(latency_ms) AS avg_ms FROM llm_calls WHERE provider = ?",
                (provider,),
            ).fetchone()
        return {"count": int(row["n"] or 0), "avg_latency_ms": row["avg_ms"]}

    def log_llm_call(
        self,
        *,
        provider: str,
        model: str | None = None,
        ok: bool = True,
        latency_ms: float | None = None,
        error: str | None = None,
    ) -> None:
        with self._connect() as con:
            con.execute(
                "INSERT INTO llm_calls (provider, model, ok, latency_ms, error, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (provider, model, 1 if ok else 0, latency_ms, error, _now()),
            )


def get_store() -> LabStore:
    global _STORE
    with _LOCK:
        if _STORE is None:
            ensure_data_dirs()
            _STORE = LabStore(DATA_DIR / "lab.db")
        return _STORE
