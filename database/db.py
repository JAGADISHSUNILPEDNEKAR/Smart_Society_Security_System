"""
Database Access Layer for Smart Society Security System.
Provides thread-safe SQLite operations, schema initialization, parameterized queries,
and administrative backup utilities.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Any, Optional
from contextlib import contextmanager

from config.settings import DEFAULT_DB_PATH, DATABASE_DIR

logger = logging.getLogger(__name__)

SCHEMA_PATH = DATABASE_DIR / "schema.sql"

class DatabaseManager:
    """Manages SQLite connections and queries with foreign key enforcement."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = str(db_path)
        self._is_memory = (self.db_path == ":memory:")
        self._shared_memory_conn: Optional[sqlite3.Connection] = None
        if self._is_memory:
            # Persistent connection for in-memory DB across calls
            self._shared_memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._shared_memory_conn.row_factory = sqlite3.Row
            self._shared_memory_conn.execute("PRAGMA foreign_keys = ON;")

    @contextmanager
    def get_connection(self):
        """Yields an SQLite connection configured with Row factory and Foreign Keys."""
        if self._is_memory:
            yield self._shared_memory_conn
            return

        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self, schema_file: Optional[Path | str] = None) -> None:
        """Initializes tables, indexes, and default settings from schema.sql."""
        path = Path(schema_file) if schema_file else SCHEMA_PATH
        if not path.exists():
            raise FileNotFoundError(f"Schema file not found at: {path}")

        schema_sql = path.read_text(encoding="utf-8")
        with self.get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()
        logger.info(f"Database initialized successfully at: {self.db_path}")

    def execute(self, query: str, params: tuple | list = ()) -> int:
        """Executes a write query (INSERT, UPDATE, DELETE) and returns rowcount or lastrowid."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount

    def fetch_one(self, query: str, params: tuple | list = ()) -> Optional[dict[str, Any]]:
        """Fetches a single row as a dictionary."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def fetch_all(self, query: str, params: tuple | list = ()) -> list[dict[str, Any]]:
        """Fetches all rows as a list of dictionaries."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieves a system setting value by key."""
        res = self.fetch_one("SELECT setting_value FROM system_settings WHERE setting_key = ?", (key,))
        return res["setting_value"] if res else default

    def set_setting(self, key: str, value: str, description: Optional[str] = None) -> None:
        """Updates or inserts a system setting value."""
        if description:
            self.execute(
                """INSERT INTO system_settings (setting_key, setting_value, description, updated_at)
                   VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(setting_key) DO UPDATE SET
                       setting_value = excluded.setting_value,
                       description = excluded.description,
                       updated_at = CURRENT_TIMESTAMP""",
                (key, str(value), description)
            )
        else:
            self.execute(
                """INSERT INTO system_settings (setting_key, setting_value, updated_at)
                   VALUES (?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(setting_key) DO UPDATE SET
                       setting_value = excluded.setting_value,
                       updated_at = CURRENT_TIMESTAMP""",
                (key, str(value))
            )

    def backup(self, target_path: Path | str) -> bool:
        """Creates an atomic SQLite backup file."""
        if self._is_memory:
            with open(target_path, "wb") as f:
                for line in self._shared_memory_conn.iterdump():
                    f.write(f"{line}\n".encode("utf-8"))
            return True

        target_str = str(target_path)
        with self.get_connection() as src_conn:
            dst_conn = sqlite3.connect(target_str)
            with dst_conn:
                src_conn.backup(dst_conn)
            dst_conn.close()
        logger.info(f"Database backed up to: {target_str}")
        return True

    def export_summary_json(self, export_path: Path | str) -> dict[str, Any]:
        """Exports an administrative summary of residents, logs, and settings to JSON."""
        summary = {
            "total_residents": self.fetch_one("SELECT COUNT(*) as c FROM residents")["c"],
            "active_residents": self.fetch_one("SELECT COUNT(*) as c FROM residents WHERE is_active = 1")["c"],
            "total_embeddings": self.fetch_one("SELECT COUNT(*) as c FROM face_embeddings")["c"],
            "total_access_logs": self.fetch_one("SELECT COUNT(*) as c FROM access_logs")["c"],
            "allowed_entries": self.fetch_one("SELECT COUNT(*) as c FROM access_logs WHERE decision = 'ENTRY ALLOWED'")["c"],
            "rejected_entries": self.fetch_one("SELECT COUNT(*) as c FROM access_logs WHERE decision = 'ENTRY REJECTED'")["c"],
            "verification_entries": self.fetch_one("SELECT COUNT(*) as c FROM access_logs WHERE decision = 'VERIFICATION REQUIRED'")["c"],
            "recent_logs": self.fetch_all("SELECT * FROM access_logs ORDER BY timestamp DESC LIMIT 20"),
            "settings": self.fetch_all("SELECT * FROM system_settings")
        }
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)
        return summary

