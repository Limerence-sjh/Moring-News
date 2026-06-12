"""Database module for Morning News.

Manages SQLite database for persisting plugin data, push logs, and daily summaries.
"""

import json
import sqlite3
import threading
from datetime import datetime, date
from typing import Dict, List, Optional


class Database:
    """SQLite database manager for Morning News.

    Args:
        db_path: Path to the SQLite database file.
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS push_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        channel TEXT NOT NULL,
        level TEXT NOT NULL,
        source TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        success BOOLEAN NOT NULL
    );

    CREATE TABLE IF NOT EXISTS bilibili_live_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        up_id TEXT NOT NULL,
        title TEXT DEFAULT '',
        is_live BOOLEAN NOT NULL,
        UNIQUE(timestamp, up_id)
    );

    CREATE TABLE IF NOT EXISTS up_names (
        up_id TEXT PRIMARY KEY,
        name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS daily_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        date DATE NOT NULL,
        data_json TEXT NOT NULL,
        UNIQUE(source, date)
    );
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None
        self._lock = threading.Lock()

    def initialize(self) -> None:
        """Create database file and tables if they don't exist."""
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(self.SCHEMA)
        self._conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection.

        Returns:
            Active SQLite connection.
        """
        with self._lock:
            if self._conn is None:
                self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
                self._conn.row_factory = sqlite3.Row
                self._conn.execute("PRAGMA journal_mode=WAL")
            return self._conn

    @staticmethod
    def _cast_bools(row_dict: dict, bool_keys: List[str]) -> dict:
        """Cast integer boolean columns to Python bool in a row dict.

        Args:
            row_dict: Dict from sqlite3.Row.
            bool_keys: Keys that should be cast to bool.

        Returns:
            Dict with boolean keys cast to Python bool.
        """
        for key in bool_keys:
            if key in row_dict:
                row_dict[key] = bool(row_dict[key])
        return row_dict

    def _get_table_names(self) -> List[str]:
        """Get list of all tables in the database.

        Returns:
            List of table names.
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        return [row["name"] for row in cursor.fetchall()]

    # --- B站直播历史记录 ---

    def save_live_record(self, up_id: str, title: str, is_live: bool) -> None:
        """Save a live room status record for a UP主.

        Args:
            up_id: B站UP主UID.
            title: Current live room title.
            is_live: Whether the UP主 is currently streaming.
        """
        with self._lock:
            conn = self._get_connection()
            conn.execute(
                "INSERT OR REPLACE INTO bilibili_live_history (timestamp, up_id, title, is_live) VALUES (?, ?, ?, ?)",
                (datetime.now().isoformat(), up_id, title, is_live)
            )
            conn.commit()

    def get_live_records(self, up_id: str, limit: int = 10) -> List[dict]:
        """Get recent live status records for a UP主.

        Args:
            up_id: B站UP主UID.
            limit: Maximum number of records to return.

        Returns:
            List of record dicts with keys: id, timestamp, up_id, title, is_live.
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT * FROM bilibili_live_history WHERE up_id=? ORDER BY timestamp ASC LIMIT ?",
                (up_id, limit)
            )
            return [Database._cast_bools(dict(row), ["is_live"]) for row in cursor.fetchall()]

    def get_last_live_status(self, up_id: str) -> Dict:
        """Get the most recent live status for a UP主.

        If no records exist, returns a default offline status.

        Args:
            up_id: B站UP主UID.

        Returns:
            Dict with keys: is_live (bool), title (str).
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT is_live, title FROM bilibili_live_history WHERE up_id=? ORDER BY timestamp DESC LIMIT 1",
                (up_id,)
            )
            row = cursor.fetchone()
            if row is None:
                return {"is_live": False, "title": ""}
            return {"is_live": bool(row["is_live"]), "title": row["title"]}

    def save_up_name(self, up_id: str, name: str) -> None:
        """Save or update UP主 display name.

        Args:
            up_id: B站UP主UID.
            name: Display name of the UP主.
        """
        with self._lock:
            conn = self._get_connection()
            conn.execute(
                "INSERT OR REPLACE INTO up_names (up_id, name) VALUES (?, ?)",
                (up_id, name)
            )
            conn.commit()

    def get_up_name(self, up_id: str) -> str:
        """Get UP主 display name, falling back to UID if not stored.

        Args:
            up_id: B站UP主UID.

        Returns:
            Display name string, or UID if name not stored.
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT name FROM up_names WHERE up_id=?",
                (up_id,)
            )
            row = cursor.fetchone()
            if row is None:
                return up_id
            return row["name"]

    # --- 每日数据 ---

    def save_daily_data(self, source: str, date: str, data: dict) -> None:
        """Save daily summary data for a source.

        Args:
            source: Plugin name (e.g., 'github_trending').
            date: Date string in YYYY-MM-DD format.
            data: Dict of daily summary data (stored as JSON).
        """
        with self._lock:
            conn = self._get_connection()
            conn.execute(
                "INSERT OR REPLACE INTO daily_data (source, date, data_json) VALUES (?, ?, ?)",
                (source, date, json.dumps(data))
            )
            conn.commit()

    def get_daily_data(self, source: str, date: str) -> Optional[dict]:
        """Get daily summary data for a source on a specific date.

        Args:
            source: Plugin name.
            date: Date string in YYYY-MM-DD format.

        Returns:
            Dict of daily data, or None if no data exists for that date.
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT data_json FROM daily_data WHERE source=? AND date=?",
                (source, date)
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return json.loads(row["data_json"])

    # --- 推送日志 ---

    def save_push_log(
        self,
        channel: str,
        level: str,
        source: str,
        title: str,
        content: str,
        success: bool
    ) -> None:
        """Record a push attempt in the log.

        Args:
            channel: Push channel ('serverchan' or 'email').
            level: Message level ('urgent' or 'daily').
            source: Plugin name that generated the message.
            title: Message title.
            content: Message content.
            success: Whether the push succeeded.
        """
        with self._lock:
            conn = self._get_connection()
            conn.execute(
                "INSERT INTO push_log (timestamp, channel, level, source, title, content, success) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (datetime.now().isoformat(), channel, level, source, title, content, success)
            )
            conn.commit()

    def get_push_count_today(self, channel: str) -> int:
        """Get the number of pushes made today through a specific channel.

        Args:
            channel: Push channel to count ('serverchan' or 'email').

        Returns:
            Number of push entries for today on that channel.
        """
        with self._lock:
            conn = self._get_connection()
            today = date.today().isoformat()
            cursor = conn.execute(
                "SELECT COUNT(*) FROM push_log WHERE channel=? AND timestamp >= ?",
                (channel, today)
            )
            row = cursor.fetchone()
            return row[0]

    def get_recent_push_logs(self, limit: int = 20) -> List[dict]:
        """Get recent push log entries.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            List of push log dicts.
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT * FROM push_log ORDER BY id ASC LIMIT ?",
                (limit,)
            )
            return [Database._cast_bools(dict(row), ["success"]) for row in cursor.fetchall()]

    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None