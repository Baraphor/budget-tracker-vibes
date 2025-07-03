# --- services/setup.py ---

from storage import get_connection


def initialize_database():
    """Create required tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER,
            include_in_budget INTEGER,
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_type TEXT,
            transaction_date TEXT,
            description TEXT,
            amount TEXT,
            category INTEGER DEFAULT 1,
            FOREIGN KEY (category) REFERENCES categories(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER UNIQUE,
            amount REAL NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_tokens (
            token TEXT PRIMARY KEY,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            ip_address TEXT,
            rate_limit INTEGER DEFAULT 100,
            window_start INTEGER DEFAULT 0,
            request_count INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()
