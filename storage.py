import sqlite3
import os
import time
import secrets
import logging

DB_PATH = os.environ.get("DB_PATH", "data/transactions.db")
CONFIG_PATH = os.environ.get("CONFIG_PATH", "data/settings.json")

DEFAULT_RATE_LIMIT = 100  # requests per minute
SESSION_EXPIRY_SECONDS = 3600

logger = logging.getLogger(__name__)

def get_connection():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        conn.row_factory = sqlite3.Row
        logger.debug("Database connection established")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}", exc_info=True)
        raise

def create_session_token(ip_address):
    token = secrets.token_hex(128)
    now = int(time.time())
    conn = get_connection()
    conn.execute("""
        INSERT INTO session_tokens (token, created_at, expires_at, ip_address, rate_limit)
        VALUES (?, ?, ?, ?, ?)
    """, (token, now, now + SESSION_EXPIRY_SECONDS, ip_address, DEFAULT_RATE_LIMIT))
    conn.commit()
    conn.close()
    logger.info(f"Session token created for IP {ip_address}")
    return token

def validate_and_track_token(token):
    conn = get_connection()
    row = conn.execute("""
        SELECT expires_at, window_start, request_count, rate_limit FROM session_tokens WHERE token = ?
    """, (token,)).fetchone()

    if not row:
        logger.warning(f"Invalid session token: {token}")
        return "invalid"

    now = int(time.time())
    if row["expires_at"] < now:
        conn.execute("DELETE FROM session_tokens WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        logger.info(f"Expired session token removed: {token}")
        return "expired"

    window_start = row["window_start"]
    request_count = row["request_count"]
    rate_limit = row["rate_limit"]

    current_window = now - (now % 60)
    if window_start != current_window:
        request_count = 1
        window_start = current_window
    else:
        if request_count >= rate_limit:
            conn.close()
            logger.warning(f"Rate limit exceeded for token: {token}")
            return "rate_limit"
        request_count += 1

    conn.execute("""
        UPDATE session_tokens SET window_start = ?, request_count = ? WHERE token = ?
    """, (window_start, request_count, token))
    conn.commit()
    conn.close()
    logger.debug(f"Session token {token} validated and updated")
    return "valid"

def get_active_token_for_ip(ip_address):
    now = int(time.time())
    conn = get_connection()
    row = conn.execute("""
        SELECT token FROM session_tokens
        WHERE ip_address = ? AND expires_at > ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (ip_address, now)).fetchone()
    conn.close()

    if row:
        logger.debug(f"Active token retrieved for IP {ip_address}")
        return row["token"]
    else:
        logger.debug(f"No active token found for IP {ip_address}")
        return None
