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
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
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
        with sqlite3.connect(self.db_path) as conn:
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
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM downloads ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def delete_record(self, record_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM downloads WHERE id = ?", (record_id,))
            conn.commit()

    def clear_all(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM downloads")
            conn.commit()
