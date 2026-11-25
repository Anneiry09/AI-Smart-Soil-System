import sqlite3
import os
import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import List, Dict, Any

OFFLINE_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "offline_buffer.db"
)


class SQLiteOfflineBuffer:
    """
    Bộ đệm lưu trữ phụ bằng SQLite khi thiết bị / trạm cục bộ mất kết nối mạng tới Server chính (VPS).
    Khi có mạng trở lại, dữ liệu chưa đồng bộ (synced = 0) sẽ được đẩy theo lô (batch) lên Server chính.
    """

    def __init__(self, db_path: str = OFFLINE_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS offline_telemetry_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    synced INTEGER NOT NULL DEFAULT 0,
                    synced_at TEXT
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_offline_synced ON offline_telemetry_queue (synced);"
            )
            conn.commit()

    def enqueue(self, payload: Dict[str, Any]) -> int:
        """Lưu bản ghi đo đạc vào hàng đợi SQLite offline khi mất mạng."""
        now_iso = datetime.utcnow().isoformat()
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO offline_telemetry_queue (device_id, payload_json, created_at, synced)
                VALUES (?, ?, ?, 0)
                """,
                (
                    payload.get("device_id", "ESP32_SOIL_01"),
                    json.dumps(payload, default=str),
                    now_iso,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def get_pending(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Lấy danh sách các bản ghi đang chờ đồng bộ lên Server chính."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT id, device_id, payload_json, created_at
                FROM offline_telemetry_queue
                WHERE synced = 0
                ORDER BY id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def mark_synced(self, ids: List[int]) -> None:
        """Đánh dấu các bản ghi đã đẩy thành công lên Server chính."""
        if not ids:
            return
        now_iso = datetime.utcnow().isoformat()
        placeholders = ",".join("?" for _ in ids)
        with self._get_conn() as conn:
            conn.execute(
                f"UPDATE offline_telemetry_queue SET synced = 1, synced_at = ? WHERE id IN ({placeholders})",
                [now_iso, *ids],
            )
            conn.commit()

    def stats(self) -> Dict[str, int]:
        """Thống kê số bản ghi chờ đồng bộ và đã đồng bộ."""
        with self._get_conn() as conn:
            pending = conn.execute(
                "SELECT COUNT(*) FROM offline_telemetry_queue WHERE synced = 0"
            ).fetchone()[0]
            synced = conn.execute(
                "SELECT COUNT(*) FROM offline_telemetry_queue WHERE synced = 1"
            ).fetchone()[0]
            return {"pending": int(pending), "synced": int(synced)}

    def sync_to_server(
        self,
        server_batch_url: str = "http://221.121.4.208/api/v1/telemetry/sync-batch",
        limit: int = 100,
        timeout_sec: int = 5,
    ) -> Dict[str, Any]:
        """Đẩy toàn bộ dữ liệu tồn đọng từ SQLite lên Server chính khi có mạng."""
        pending_rows = self.get_pending(limit=limit)
        if not pending_rows:
            return {"status": "idle", "synced_count": 0, "remaining": 0}

        records = [json.loads(r["payload_json"]) for r in pending_rows]
        body = json.dumps({"records": records}).encode("utf-8")
        req = urllib.request.Request(
            server_batch_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                if resp.status in (200, 201):
                    self.mark_synced([r["id"] for r in pending_rows])
                    current_stats = self.stats()
                    return {
                        "status": "synced",
                        "synced_count": len(pending_rows),
                        "remaining": current_stats["pending"],
                    }
        except (urllib.error.URLError, TimeoutError, Exception) as exc:
            return {
                "status": "offline",
                "synced_count": 0,
                "remaining": self.stats()["pending"],
                "error": str(exc),
            }

        return {"status": "failed", "synced_count": 0, "remaining": self.stats()["pending"]}


offline_buffer = SQLiteOfflineBuffer()
