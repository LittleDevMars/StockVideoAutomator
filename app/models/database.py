import sqlite3
import os
from datetime import datetime


class DownloadDatabase:
    def __init__(self, db_path: str = None):
        if db_path is None:
            app_data = os.path.join(os.path.expanduser("~"), ".youtube_downloader")
            os.makedirs(app_data, exist_ok=True)
            db_path = os.path.join(app_data, "downloads.db")
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Return the persistent connection, creating it if needed."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                video_id TEXT,
                title TEXT,
                channel TEXT,
                thumbnail_url TEXT,
                file_path TEXT,
                format TEXT,
                quality TEXT,
                filesize INTEGER,
                duration INTEGER,
                download_type TEXT DEFAULT 'video',
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    def add_record(self, url: str, video_id: str, title: str, channel: str,
                   thumbnail_url: str, file_path: str, fmt: str, quality: str,
                   filesize: int, duration: int, download_type: str = "video"):
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO downloads
               (url, video_id, title, channel, thumbnail_url, file_path,
                format, quality, filesize, duration, download_type, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?)""",
            (url, video_id, title, channel, thumbnail_url, file_path,
             fmt, quality, filesize, duration, download_type,
             datetime.now().isoformat()),
        )
        conn.commit()

    def get_all_records(self, limit: int = 100) -> list:
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM downloads ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def delete_record(self, record_id: int):
        conn = self._get_conn()
        conn.execute("DELETE FROM downloads WHERE id = ?", (record_id,))
        conn.commit()

    def clear_all(self):
        conn = self._get_conn()
        conn.execute("DELETE FROM downloads")
        conn.commit()

    def close(self):
        """Close the persistent connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
