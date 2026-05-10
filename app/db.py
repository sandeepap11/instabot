import sqlite3
import uuid
from datetime import datetime
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets you access columns by name
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id          TEXT PRIMARY KEY,
                niche       TEXT NOT NULL,
                prompt      TEXT NOT NULL,
                caption     TEXT NOT NULL,
                image_path  TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'pending',
                created_at  TEXT NOT NULL,
                posted_at   TEXT
            )
        """)
        conn.commit()
    print("[DB] Initialised.")


def save_post(niche, prompt, caption, image_path) -> str:
    post_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO posts (id, niche, prompt, caption, image_path, status, created_at)
               VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
            (post_id, niche, prompt, caption,
             image_path, datetime.now().isoformat())
        )
        conn.commit()
    print(f"[DB] Saved post {post_id} as pending.")
    return post_id


def get_pending_posts():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM posts WHERE status = 'pending' ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_approved_posts():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM posts WHERE status = 'approved' ORDER BY created_at ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def update_status(post_id: str, status: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE posts SET status = ? WHERE id = ?",
            (status, post_id)
        )
        conn.commit()
    print(f"[DB] Post {post_id} → {status}")


def mark_posted(post_id: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE posts SET status = 'posted', posted_at = ? WHERE id = ?",
            (datetime.now().isoformat(), post_id)
        )
        conn.commit()
    print(f"[DB] Post {post_id} → posted")


def get_all_posts():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM posts ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]
