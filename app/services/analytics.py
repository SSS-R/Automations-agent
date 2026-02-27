"""
Lightweight SQLite analytics for tracking pipeline runs and clip generation.
No external dependencies — uses Python's built-in sqlite3.
"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager

DB_PATH = Path("data") / "analytics.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent read performance
    return conn


@contextmanager
def _db():
    """Context manager for database connections."""
    conn = _get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with _db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_url TEXT NOT NULL,
                video_title TEXT,
                video_id TEXT,
                clips_generated INTEGER DEFAULT 0,
                duration_seconds REAL,
                status TEXT DEFAULT 'started',
                created_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                clip_idx INTEGER,
                viral_score INTEGER,
                start_time TEXT,
                end_time TEXT,
                hook TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES pipeline_runs(id)
            );
        """)


def record_pipeline_start(video_url: str, video_title: str = None, video_id: str = None) -> int:
    """Record the start of a pipeline run. Returns the run ID."""
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    with _db() as conn:
        cursor = conn.execute(
            "INSERT INTO pipeline_runs (video_url, video_title, video_id, status, created_at) VALUES (?, ?, ?, 'processing', ?)",
            (video_url, video_title, video_id, now)
        )
        return cursor.lastrowid


def record_pipeline_complete(run_id: int, clips_generated: int):
    """Mark a pipeline run as completed."""
    now = datetime.now(timezone.utc).isoformat()
    with _db() as conn:
        conn.execute(
            "UPDATE pipeline_runs SET status = 'completed', clips_generated = ?, completed_at = ? WHERE id = ?",
            (clips_generated, now, run_id)
        )


def record_pipeline_failed(run_id: int, error: str = None):
    """Mark a pipeline run as failed."""
    now = datetime.now(timezone.utc).isoformat()
    with _db() as conn:
        conn.execute(
            "UPDATE pipeline_runs SET status = 'failed', completed_at = ? WHERE id = ?",
            (now, run_id)
        )


def record_clip(run_id: int, clip_idx: int, viral_score: int = None,
                start_time: str = None, end_time: str = None, hook: str = None):
    """Record a generated clip."""
    now = datetime.now(timezone.utc).isoformat()
    with _db() as conn:
        conn.execute(
            "INSERT INTO clips (run_id, clip_idx, viral_score, start_time, end_time, hook, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, clip_idx, viral_score, start_time, end_time, hook, now)
        )


def get_stats() -> dict:
    """Get aggregate statistics for the dashboard."""
    init_db()
    with _db() as conn:
        # Total counts
        total_videos = conn.execute(
            "SELECT COUNT(*) FROM pipeline_runs WHERE status = 'completed'"
        ).fetchone()[0]
        
        total_clips = conn.execute(
            "SELECT COALESCE(SUM(clips_generated), 0) FROM pipeline_runs WHERE status = 'completed'"
        ).fetchone()[0]
        
        # Today's counts (UTC)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_videos = conn.execute(
            "SELECT COUNT(*) FROM pipeline_runs WHERE status = 'completed' AND created_at LIKE ?",
            (f"{today}%",)
        ).fetchone()[0]
        
        today_clips = conn.execute(
            "SELECT COALESCE(SUM(clips_generated), 0) FROM pipeline_runs WHERE status = 'completed' AND created_at LIKE ?",
            (f"{today}%",)
        ).fetchone()[0]
        
        # Last processed
        last_run = conn.execute(
            "SELECT video_title, completed_at FROM pipeline_runs WHERE status = 'completed' ORDER BY completed_at DESC LIMIT 1"
        ).fetchone()
        
        # Average viral score
        avg_score = conn.execute(
            "SELECT ROUND(AVG(viral_score), 1) FROM clips WHERE viral_score IS NOT NULL"
        ).fetchone()[0]

        return {
            "total_videos": total_videos,
            "total_clips": total_clips,
            "today_videos": today_videos,
            "today_clips": today_clips,
            "avg_viral_score": avg_score or 0,
            "last_processed_title": last_run["video_title"] if last_run else None,
            "last_processed_at": last_run["completed_at"] if last_run else None,
        }
