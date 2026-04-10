"""
SMS Telegram Bot – Database Module
=====================================
Provides a thin SQLite3 data-access layer for:

* **User profiles**    – registration, last-seen timestamp.
* **Ban list**         – admins can block/unblock users.
* **Daily SMS quota**  – reset automatically each calendar day; enforces the
                         MAX_SMS_PER_DAY rate limit.
* **SMS audit log**    – every send attempt is persisted with its Infobip
                         message-ID and delivery status.

All public functions accept a *db_path* parameter so the correct database file
can be passed in from config.py (or overridden in tests).

Example
-------
>>> from database import init_db, register_user, check_and_increment_quota
>>> init_db("./data/sms_bot.db")
>>> register_user("./data/sms_bot.db", telegram_id=123, username="alice", first_name="Alice")
>>> allowed = check_and_increment_quota("./data/sms_bot.db", 123, max_per_day=10)
"""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from typing import Dict, Generator, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Schema DDL
# ─────────────────────────────────────────────────────────────────────────────

_DDL = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id   INTEGER PRIMARY KEY,
    username      TEXT,
    first_name    TEXT,
    is_banned     INTEGER NOT NULL DEFAULT 0,
    daily_count   INTEGER NOT NULL DEFAULT 0,
    quota_date    TEXT,                      -- ISO date of last quota window
    total_sent    INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL,
    last_seen     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sms_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id     INTEGER NOT NULL,
    recipient     TEXT NOT NULL,
    message       TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'pending',
    message_id    TEXT,                      -- Infobip message ID
    error         TEXT,
    sent_at       TEXT NOT NULL
);
"""


# ─────────────────────────────────────────────────────────────────────────────
# Connection helper
# ─────────────────────────────────────────────────────────────────────────────


@contextmanager
def _connect(db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """
    Yield a SQLite connection with WAL mode and foreign-key support enabled.

    The connection is committed and closed on exit; any exception triggers a
    rollback automatically (standard sqlite3 context-manager behaviour).
    """
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Initialisation
# ─────────────────────────────────────────────────────────────────────────────


def init_db(db_path: str) -> None:
    """
    Create the database tables if they do not already exist.

    Safe to call on every startup; it is idempotent due to
    ``CREATE TABLE IF NOT EXISTS``.

    Parameters
    ----------
    db_path:
        Absolute or relative path to the SQLite file.
    """
    with _connect(db_path) as conn:
        conn.executescript(_DDL)
    logger.info("Database initialised at %s", db_path)


# ─────────────────────────────────────────────────────────────────────────────
# User management
# ─────────────────────────────────────────────────────────────────────────────


def register_user(
    db_path: str,
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
) -> None:
    """
    Insert or update a user row, refreshing *last_seen* on every call.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.
    telegram_id:
        Unique numeric Telegram user identifier.
    username:
        Telegram @username (may be ``None``).
    first_name:
        Display name from Telegram (may be ``None``).
    """
    now = _now()
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO users (telegram_id, username, first_name, created_at, last_seen)
            VALUES (:tid, :uname, :fname, :now, :now)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name,
                last_seen  = excluded.last_seen
            """,
            {"tid": telegram_id, "uname": username, "fname": first_name, "now": now},
        )
    logger.debug("register_user: telegram_id=%d", telegram_id)


def get_user(db_path: str, telegram_id: int) -> Optional[Dict]:
    """
    Return a dictionary of a user's profile, or *None* if not found.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.
    telegram_id:
        Telegram user identifier to look up.
    """
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
    return dict(row) if row else None


def get_all_users(db_path: str) -> List[Dict]:
    """
    Return every user profile stored in the database.

    Typically called by admin commands such as ``/users``.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.
    """
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM users ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# Ban / unban
# ─────────────────────────────────────────────────────────────────────────────


def is_banned(db_path: str, telegram_id: int) -> bool:
    """
    Return ``True`` when the user is currently banned.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.
    telegram_id:
        Telegram user identifier to check.
    """
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT is_banned FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
    return bool(row["is_banned"]) if row else False


def ban_user(db_path: str, telegram_id: int) -> bool:
    """
    Mark a user as banned.

    Returns ``True`` if the user existed (and was updated), ``False`` if no
    matching user was found.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.
    telegram_id:
        Telegram user identifier to ban.
    """
    with _connect(db_path) as conn:
        cur = conn.execute(
            "UPDATE users SET is_banned = 1 WHERE telegram_id = ?", (telegram_id,)
        )
    updated = cur.rowcount > 0
    logger.info("ban_user: telegram_id=%d updated=%s", telegram_id, updated)
    return updated


def unban_user(db_path: str, telegram_id: int) -> bool:
    """
    Remove a ban from a user.

    Returns ``True`` if the user existed (and was updated).

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.
    telegram_id:
        Telegram user identifier to unban.
    """
    with _connect(db_path) as conn:
        cur = conn.execute(
            "UPDATE users SET is_banned = 0 WHERE telegram_id = ?", (telegram_id,)
        )
    updated = cur.rowcount > 0
    logger.info("unban_user: telegram_id=%d updated=%s", telegram_id, updated)
    return updated


# ─────────────────────────────────────────────────────────────────────────────
# Daily SMS quota
# ─────────────────────────────────────────────────────────────────────────────


def check_and_increment_quota(
    db_path: str, telegram_id: int, max_per_day: int
) -> Tuple[bool, int]:
    """
    Atomically check whether *telegram_id* is within the daily SMS quota and,
    if so, increment their counter.

    The quota window resets to zero whenever ``quota_date`` differs from
    today's date (UTC).

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.
    telegram_id:
        Telegram user identifier.
    max_per_day:
        Maximum allowed SMS sends per calendar day.

    Returns
    -------
    (allowed, current_count)
        *allowed* is ``True`` when the send may proceed.
        *current_count* is the updated daily counter (after incrementing) when
        *allowed* is ``True``, or the current counter when *allowed* is
        ``False``.
    """
    today = date.today().isoformat()

    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT daily_count, quota_date FROM users WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()

        if row is None:
            # Unknown user – allow but don't mutate (caller should register first)
            return True, 0

        current_date: Optional[str] = row["quota_date"]
        current_count: int = row["daily_count"] if current_date == today else 0

        if current_count >= max_per_day:
            return False, current_count

        new_count = current_count + 1
        conn.execute(
            "UPDATE users SET daily_count = ?, quota_date = ?, total_sent = total_sent + 1 WHERE telegram_id = ?",
            (new_count, today, telegram_id),
        )

    logger.debug(
        "check_and_increment_quota: telegram_id=%d count=%d/%d",
        telegram_id,
        new_count,
        max_per_day,
    )
    return True, new_count


def get_daily_usage(db_path: str, telegram_id: int) -> Tuple[int, str]:
    """
    Return (daily_count, quota_date) for *telegram_id*.

    If the stored date is not today the effective count is zero.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.
    telegram_id:
        Telegram user identifier.
    """
    today = date.today().isoformat()
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT daily_count, quota_date FROM users WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()

    if not row:
        return 0, today

    count = row["daily_count"] if row["quota_date"] == today else 0
    return count, row["quota_date"] or today


# ─────────────────────────────────────────────────────────────────────────────
# SMS audit log
# ─────────────────────────────────────────────────────────────────────────────


def log_sms(
    db_path: str,
    sender_id: int,
    recipient: str,
    message: str,
    status: str,
    message_id: Optional[str] = None,
    error: Optional[str] = None,
) -> int:
    """
    Persist a send attempt to the ``sms_log`` table.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.
    sender_id:
        Telegram user identifier of the sender.
    recipient:
        Formatted phone number (E.164 form, e.g. ``+85512345678``).
    message:
        SMS body text.
    status:
        ``"sent"``, ``"failed"``, or ``"pending"``.
    message_id:
        Infobip message ID if the API call succeeded.
    error:
        Human-readable error description if the send failed.

    Returns
    -------
    int
        The ``rowid`` / ``id`` of the newly inserted row.
    """
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO sms_log (sender_id, recipient, message, status, message_id, error, sent_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (sender_id, recipient, message, status, message_id, error, _now()),
        )
    logger.debug(
        "log_sms: sender=%d recipient=%s status=%s", sender_id, recipient, status
    )
    return cur.lastrowid  # type: ignore[return-value]


def get_user_sms_history(
    db_path: str, telegram_id: int, limit: int = 20
) -> List[Dict]:
    """
    Return the most recent SMS log entries for *telegram_id*.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.
    telegram_id:
        Telegram user identifier.
    limit:
        Maximum number of rows to return (most-recent first).
    """
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM sms_log
            WHERE sender_id = ?
            ORDER BY sent_at DESC
            LIMIT ?
            """,
            (telegram_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# Global statistics (admin)
# ─────────────────────────────────────────────────────────────────────────────


def get_global_stats(db_path: str) -> Dict:
    """
    Return a dictionary of aggregate statistics across all users.

    Returned keys
    -------------
    total_users     – total registered user count.
    banned_users    – number of currently banned users.
    total_sms_sent  – sum of all successful sends across all users.
    today_sms_sent  – sends recorded today (UTC date).

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.
    """
    today = date.today().isoformat()
    with _connect(db_path) as conn:
        total_users: int = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        banned_users: int = conn.execute(
            "SELECT COUNT(*) FROM users WHERE is_banned = 1"
        ).fetchone()[0]
        total_sms: int = conn.execute(
            "SELECT COALESCE(SUM(total_sent), 0) FROM users"
        ).fetchone()[0]
        today_sms: int = conn.execute(
            "SELECT COUNT(*) FROM sms_log WHERE sent_at LIKE ? AND status = 'sent'",
            (today + "%",),
        ).fetchone()[0]

    return {
        "total_users": total_users,
        "banned_users": banned_users,
        "total_sms_sent": total_sms,
        "today_sms_sent": today_sms,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────


def _now() -> str:
    """Return the current UTC datetime as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
