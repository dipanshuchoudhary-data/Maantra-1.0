import sqlite3
import json
import time
import random
import string
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

# ---------------------------------------------------------
# Database initialization
# ---------------------------------------------------------

DB_PATH = Path("data/assistant.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

db = sqlite3.connect(DB_PATH, check_same_thread=False)
db.row_factory = sqlite3.Row


def init_schema():
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            channel_id TEXT,
            thread_ts TEXT,
            session_type TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            last_activity INTEGER NOT NULL,
            metadata TEXT
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            slack_ts TEXT,
            thread_ts TEXT,
            created_at INTEGER NOT NULL,
            metadata TEXT
        );

        CREATE TABLE IF NOT EXISTS scheduled_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            thread_ts TEXT,
            task_description TEXT NOT NULL,
            cron_expression TEXT,
            scheduled_time INTEGER,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at INTEGER NOT NULL,
            executed_at INTEGER,
            metadata TEXT
        );

        CREATE TABLE IF NOT EXISTS pairing_codes (
            code TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            approved INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS approved_users (
            user_id TEXT PRIMARY KEY,
            approved_at INTEGER NOT NULL,
            approved_by TEXT
        );
        """
    )
    db.commit()


init_schema()


def initialize_database():
    """
    Initialize the SQLite database and schema.
    Safe to call multiple times.
    """
    init_schema()

# ---------------------------------------------------------
# Session management
# ---------------------------------------------------------


def get_or_create_session(user_id: str, channel_id: Optional[str], thread_ts: Optional[str]):
    if thread_ts:
        session_id = f"thread:{channel_id}:{thread_ts}"
        session_type = "thread"
    elif channel_id and not channel_id.startswith("D"):
        session_id = f"channel:{channel_id}"
        session_type = "channel"
    else:
        session_id = f"dm:{user_id}"
        session_type = "dm"

    row = db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()

    if row:
        db.execute(
            "UPDATE sessions SET last_activity=? WHERE id=?",
            (int(time.time()), session_id),
        )
        db.commit()
        return dict(row)

    db.execute(
        """
        INSERT INTO sessions
        (id, user_id, channel_id, thread_ts, session_type, created_at, last_activity)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            user_id,
            channel_id,
            thread_ts,
            session_type,
            int(time.time()),
            int(time.time()),
        ),
    )
    db.commit()

    return {
        "id": session_id,
        "user_id": user_id,
        "channel_id": channel_id,
        "thread_ts": thread_ts,
        "session_type": session_type,
    }


def get_session_metadata(session_id: str) -> Dict[str, Any]:

    row = db.execute(
        "SELECT metadata FROM sessions WHERE id = ?",
        (session_id,),
    ).fetchone()

    if not row:
        return {}

    raw = row["metadata"]

    if not raw:
        return {}

    try:
        return json.loads(raw)
    except Exception:
        return {}


def update_session_metadata(session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:

    current = get_session_metadata(session_id)
    merged = {**current, **updates}

    db.execute(
        "UPDATE sessions SET metadata = ?, last_activity = ? WHERE id = ?",
        (json.dumps(merged), int(time.time()), session_id),
    )
    db.commit()

    return merged


# ---------------------------------------------------------
# Message history
# ---------------------------------------------------------


def add_message(
    session_id: str,
    role: str,
    content: str,
    slack_ts: Optional[str] = None,
    thread_ts: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):

    db.execute(
        """
        INSERT INTO messages
        (session_id, role, content, slack_ts, thread_ts, created_at, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            role,
            content,
            slack_ts,
            thread_ts,
            int(time.time()),
            json.dumps(metadata) if metadata else None,
        ),
    )
    db.commit()


def get_session_history(session_id: str, limit: int = 50):
    rows = db.execute(
        """
        SELECT * FROM messages
        WHERE session_id=?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (session_id, limit),
    ).fetchall()

    return [dict(r) for r in reversed(rows)]


def clear_session_history(session_id: str):
    db.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
    db.commit()


# ---------------------------------------------------------
# Scheduled tasks
# ---------------------------------------------------------


def create_scheduled_task(
    user_id: str,
    channel_id: str,
    task_description: str,
    scheduled_time: Optional[int] = None,
    cron_expression: Optional[str] = None,
    thread_ts: Optional[str] = None,
):

    cur = db.execute(
        """
        INSERT INTO scheduled_tasks
        (user_id, channel_id, thread_ts, task_description, cron_expression, scheduled_time, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            channel_id,
            thread_ts,
            task_description,
            cron_expression,
            scheduled_time,
            int(time.time()),
        ),
    )

    db.commit()

    return cur.lastrowid


def get_pending_tasks():
    now = int(time.time())

    rows = db.execute(
        """
        SELECT *
        FROM scheduled_tasks
        WHERE status='pending'
        AND (scheduled_time IS NULL OR scheduled_time <= ?)
        ORDER BY scheduled_time ASC
        """,
        (now,),
    ).fetchall()

    return [dict(r) for r in rows]


def update_task_status(task_id: int, status: str):
    now = int(time.time())

    db.execute(
        """
        UPDATE scheduled_tasks
        SET status=?,
            executed_at = CASE
                WHEN ? IN ('completed','failed') THEN ?
                ELSE executed_at
            END
        WHERE id=?
        """,
        (status, status, now, task_id),
    )

    db.commit()


def get_user_tasks(user_id: str):

    rows = db.execute(
        """
        SELECT *
        FROM scheduled_tasks
        WHERE user_id=?
        ORDER BY created_at DESC
        LIMIT 20
        """,
        (user_id,),
    ).fetchall()

    return [dict(r) for r in rows]


def cancel_task(task_id: int, user_id: str):

    cur = db.execute(
        """
        UPDATE scheduled_tasks
        SET status='cancelled'
        WHERE id=? AND user_id=? AND status='pending'
        """,
        (task_id, user_id),
    )

    db.commit()

    return cur.rowcount > 0


# ---------------------------------------------------------
# Pairing security
# ---------------------------------------------------------


def generate_pairing_code(user_id: str):

    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    expires = int(time.time()) + 3600

    db.execute("DELETE FROM pairing_codes WHERE user_id=?", (user_id,))

    db.execute(
        """
        INSERT INTO pairing_codes (code, user_id, created_at, expires_at)
        VALUES (?, ?, ?, ?)
        """,
        (code, user_id, int(time.time()), expires),
    )

    db.commit()

    return code


def verify_pairing_code(code: str):

    row = db.execute(
        """
        SELECT user_id
        FROM pairing_codes
        WHERE code=? AND expires_at>? AND approved=0
        """,
        (code.upper(), int(time.time())),
    ).fetchone()

    return row["user_id"] if row else None


def approve_pairing(code: str, approved_by: str):

    user_id = verify_pairing_code(code)

    if not user_id:
        return False

    db.execute(
        "UPDATE pairing_codes SET approved=1 WHERE code=?",
        (code.upper(),),
    )

    db.execute(
        """
        INSERT OR REPLACE INTO approved_users
        (user_id, approved_at, approved_by)
        VALUES (?, ?, ?)
        """,
        (user_id, int(time.time()), approved_by),
    )

    db.commit()

    return True


def is_user_approved(user_id: str):

    row = db.execute(
        "SELECT 1 FROM approved_users WHERE user_id=?",
        (user_id,),
    ).fetchone()

    return bool(row)


# ---------------------------------------------------------
# Cleanup
# ---------------------------------------------------------


def cleanup_old_sessions(max_age_seconds: int = 604800):

    cutoff = int(time.time()) - max_age_seconds

    cur = db.execute(
        "DELETE FROM sessions WHERE last_activity < ?",
        (cutoff,),
    )

    db.commit()

    return cur.rowcount


def cleanup_expired_pairing_codes():

    now = int(time.time())

    cur = db.execute(
        "DELETE FROM pairing_codes WHERE expires_at < ? AND approved=0",
        (now,),
    )

    db.commit()

    return cur.rowcount


# ---------------------------------------------------------
# Shutdown
# ---------------------------------------------------------


def close_database():
    db.close()