import pandas as pd
import logging
from storage import get_connection

logger = logging.getLogger(__name__)

# ---------------- Transactions ----------------

def get_all_transactions():
    conn = get_connection()
    df = pd.read_sql_query('''
        SELECT t.id, t.account_type, t.transaction_date, t.description,
               t.amount, t.category, c.name AS category_name
        FROM transactions t
        LEFT JOIN categories c ON t.category = c.id
        ORDER BY t.transaction_date DESC
    ''', conn)
    conn.close()
    logger.debug("Retrieved all transactions")
    return df

def update_transaction_category(transaction_id, category_id):
    conn = get_connection()
    conn.execute("UPDATE transactions SET category = ? WHERE id = ?", (category_id, transaction_id))
    conn.commit()
    conn.close()
    logger.info(f"Transaction {transaction_id} category updated to {category_id}")

def update_transaction_description(transaction_id, description):
    conn = get_connection()
    conn.execute("UPDATE transactions SET description = ? WHERE id = ?", (description, transaction_id))
    conn.commit()
    conn.close()
    logger.info(f"Transaction {transaction_id} description updated")

def insert_transaction(data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (account_type, transaction_date, description, amount, category)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        data["account_type"],
        data["transaction_date"],
        data["description"],
        data["amount"],
        data["category"]
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    logger.info(f"Transaction inserted with ID {new_id}")
    return new_id

def get_transaction_by_id(transaction_id):
    conn = get_connection()
    df = pd.read_sql_query('''
        SELECT t.id, t.transaction_date, t.account_type,
               t.description AS description, t.amount, c.name AS category_name
        FROM transactions t
        LEFT JOIN categories c ON t.category = c.id
        WHERE t.id = ?
    ''', conn, params=(transaction_id,))
    conn.close()

    if df.empty:
        logger.warning(f"Transaction {transaction_id} not found")
        return {}
    logger.debug(f"Transaction {transaction_id} retrieved")
    return df.iloc[0].to_dict()

def delete_transaction_by_id(transaction_id):
    conn = get_connection()
    conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()
    logger.info(f"Transaction {transaction_id} deleted")

def clear_all_transactions():
    conn = get_connection()
    conn.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()
    logger.info("All transactions cleared")

def get_all_transaction_months():
    conn = get_connection()
    df = pd.read_sql_query("SELECT transaction_date FROM transactions", conn)
    conn.close()
    logger.debug("Retrieved all transaction months")
    return df

def get_most_recent_transaction_month():
    conn = get_connection()
    df = pd.read_sql_query('''
        SELECT strftime('%Y-%m', MAX(transaction_date)) AS latest_month
        FROM transactions
    ''', conn)
    conn.close()
    month = df.iloc[0]["latest_month"] if not df.empty else None
    logger.debug(f"Most recent transaction month: {month}")
    return month

def get_existing_transaction_records():
    conn = get_connection()
    try:
        df = pd.read_sql_query('''
            SELECT account_type, transaction_date, description, amount 
            FROM transactions
        ''', conn)
        logger.debug("Existing transaction records retrieved")
    except Exception as e:
        df = pd.DataFrame()
        logger.error(f"Error retrieving existing transaction records: {e}", exc_info=True)
    conn.close()
    return df

def transaction_exists(transaction_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM transactions WHERE id = ?", (transaction_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    logger.debug(f"Transaction {transaction_id} existence check: {exists}")
    return exists

# ---------------- Categories ----------------

def get_all_categories():
    conn = get_connection()
    df = pd.read_sql_query("SELECT id, name, parent_id, include_in_budget FROM categories", conn)
    conn.close()
    logger.debug("Retrieved all categories")
    return df

def insert_category(name, parent_id=None):
    conn = get_connection()
    conn.execute('''
        INSERT INTO categories (name, parent_id, include_in_budget)
        VALUES (?, ?, ?)
    ''', (name, parent_id, 1))
    conn.commit()
    conn.close()
    logger.info(f"Category '{name}' inserted with parent {parent_id}")

def delete_category(category_id):
    conn = get_connection()
    conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()
    logger.info(f"Category {category_id} deleted")

def update_category_name(category_id, new_name):
    conn = get_connection()
    conn.execute("UPDATE categories SET name = ? WHERE id = ?", (new_name, category_id))
    conn.commit()
    conn.close()
    logger.info(f"Category {category_id} renamed to '{new_name}'")

def toggle_include_in_budget(category_id):
    conn = get_connection()
    conn.execute("""
        UPDATE categories
        SET include_in_budget = CASE WHEN include_in_budget = 1 THEN 0 ELSE 1 END
        WHERE id = ?
    """, (category_id,))
    conn.commit()
    conn.close()
    logger.info(f"Category {category_id} include_in_budget toggled")

def get_category(category_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, parent_id FROM categories WHERE id = ?", (category_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        logger.debug(f"Category {category_id} retrieved")
        return {"id": row[0], "name": row[1], "parent_id": row[2]}
    else:
        logger.warning(f"Category {category_id} not found")
        return None

# ---------------- Budgets ----------------

def update_budget_amount(category_id, amount):
    conn = get_connection()
    conn.execute('''
        INSERT INTO budgets (category_id, amount)
        VALUES (?, ?)
        ON CONFLICT(category_id) DO UPDATE SET amount = excluded.amount
    ''', (category_id, amount))
    conn.commit()
    conn.close()
    logger.info(f"Budget for category {category_id} updated to {amount}")

def get_budget_status(month):
    conn = get_connection()
    query = '''
        SELECT 
            c.id AS category_id,
            c.name AS category,
            c.parent_id,
            IFNULL(b.amount, 0.00) AS budget,
            IFNULL((
                SELECT SUM(ABS(t.amount))
                FROM transactions t
                WHERE t.category = c.id
                AND strftime('%Y-%m', t.transaction_date) = ?
            ), 0.00) AS spent
        FROM categories c
        LEFT JOIN categories p ON c.parent_id = p.id
        LEFT JOIN budgets b ON b.category_id = c.id
        WHERE COALESCE(p.include_in_budget, c.include_in_budget) = 1
    '''
    df = pd.read_sql_query(query, conn, params=(month,))
    conn.close()
    logger.debug(f"Budget status retrieved for month {month}")
    return df

# ---------------- Graphs & Summaries ----------------

def get_graph_data_for_month():
    conn = get_connection()
    df = pd.read_sql_query('''
        SELECT t.transaction_date, t.amount, c.name AS category_name,
               c.id AS category_id, c.parent_id, p.name AS parent_name
        FROM transactions t
        LEFT JOIN categories c ON t.category = c.id
        LEFT JOIN categories p ON c.parent_id = p.id
        WHERE t.amount IS NOT NULL
    ''', conn)
    conn.close()
    logger.debug("Graph data retrieved")
    return df

def get_available_months():
    conn = get_connection()
    df = pd.read_sql_query("SELECT transaction_date FROM transactions", conn)
    conn.close()
    logger.debug("Available months retrieved")
    return df

def get_income_expense_by_month():
    conn = get_connection()
    df = pd.read_sql_query("SELECT transaction_date, amount FROM transactions", conn)
    conn.close()
    logger.debug("Income and expense by month retrieved")
    return df
