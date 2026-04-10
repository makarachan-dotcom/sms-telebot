"""
SMS Telegram Bot – Configuration Module
========================================
Loads all runtime settings from environment variables (via dotenv).

Environment variables read
--------------------------
TELEGRAM_TOKEN / TELEGRAM_BOT_TOKEN  – Telegram Bot API token (required).
INFOBIP_API_KEY                      – Infobip API key (required for SMS).
INFOBIP_BASE_URL                     – Infobip base URL, e.g. https://XXXX.api.infobip.com
ADMIN_USER_IDS                       – Comma-separated Telegram user IDs with admin rights.
MAX_SMS_PER_DAY                      – Maximum SMS a single user may send per calendar day
                                       (default: 10).
DATA_DIR                             – Directory used for the SQLite database (default: ./data).
LOG_DIR                              – Directory for log files (default: ./logs).
LOG_LEVEL                            – Python logging level string (default: INFO).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────────────────
# Load .env file (if present).  Variables already in the real environment take
# precedence thanks to the default override=False behaviour.
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Telegram
# ─────────────────────────────────────────────────────────────────────────────
# Support both variable names so the existing bot startup continues to work.
TELEGRAM_TOKEN: str = (
    os.environ.get("TELEGRAM_TOKEN")
    or os.environ.get("TELEGRAM_BOT_TOKEN")
    or ""
)

# ─────────────────────────────────────────────────────────────────────────────
# Infobip
# ─────────────────────────────────────────────────────────────────────────────
INFOBIP_API_KEY: str = os.environ.get("INFOBIP_API_KEY", "")
INFOBIP_BASE_URL: str = os.environ.get("INFOBIP_BASE_URL", "").rstrip("/")
"""
Base URL looks like https://XXXX.api.infobip.com  (no trailing slash).
Obtain it from https://portal.infobip.com/dev/api-keys after creating a key.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Admin
# ─────────────────────────────────────────────────────────────────────────────
ADMIN_USER_IDS: List[int] = []
_admin_str: str = os.environ.get("ADMIN_USER_IDS", "")
if _admin_str:
    ADMIN_USER_IDS = [
        int(x.strip())
        for x in _admin_str.split(",")
        if x.strip().lstrip("-").isdigit()
    ]

# ─────────────────────────────────────────────────────────────────────────────
# Rate limiting
# ─────────────────────────────────────────────────────────────────────────────
MAX_SMS_PER_DAY: int = int(os.environ.get("MAX_SMS_PER_DAY", "10"))
"""Maximum number of SMS messages a single (non-admin) user may send per day."""

# ─────────────────────────────────────────────────────────────────────────────
# Filesystem paths
# ─────────────────────────────────────────────────────────────────────────────
DATA_DIR: Path = Path(os.environ.get("DATA_DIR", "./data"))
DB_PATH: str = str(DATA_DIR / "sms_bot.db")

LOG_DIR: Path = Path(os.environ.get("LOG_DIR", "./logs"))
LOG_FILE: str = str(LOG_DIR / "sms_bot.log")

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()


def ensure_directories() -> None:
    """Create DATA_DIR and LOG_DIR if they do not already exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def configure_logging() -> None:
    """
    Set up file + console logging for the whole application.

    * Console handler  – writes INFO (or LOG_LEVEL) messages with colour-like
      formatting to stdout.
    * File handler     – writes DEBUG messages to LOG_FILE with full detail.
    """
    ensure_directories()

    numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)

    fmt_verbose = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    fmt_concise = "%(asctime)s %(levelname)s %(name)s: %(message)s"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # capture everything; handlers filter

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(logging.Formatter(fmt_concise, datefmt="%H:%M:%S"))

    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(fmt_verbose))

    # Avoid duplicate handlers if configure_logging() is called more than once
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
    else:
        # Replace existing handlers with ours only if they are still the default
        root_logger.handlers.clear()
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
