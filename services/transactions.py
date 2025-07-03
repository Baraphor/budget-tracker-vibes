import db_queries
import pandas as pd

def get_transactions():
    """Fetch transactions with any additional processing."""
    df = db_queries.get_all_transactions()
    return df


def update_transaction_category(transaction_id, category_id):
    """Assign a category to a transaction."""
    db_queries.update_transaction_category(transaction_id, category_id)


def update_transaction_description(transaction_id, description):
    """Update the transaction description."""
    db_queries.update_transaction_description(transaction_id, description)


def add_transaction(data):
    """Add a new transaction and return its ID."""
    return db_queries.insert_transaction(data)


def get_transaction(transaction_id):
    """Retrieve a specific transaction by ID."""
    return db_queries.get_transaction_by_id(transaction_id)


def delete_transaction(transaction_id):
    """Delete a transaction."""
    db_queries.delete_transaction_by_id(transaction_id)


def clear_all_transactions():
    """Delete all transactions from the database."""
    db_queries.clear_all_transactions()


def get_transaction_months():
    """Fetch all months with transactions."""
    df = db_queries.get_all_transaction_months()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df = df.dropna()
    months = df["transaction_date"].dt.to_period("M").astype(str).unique().tolist()
    months.sort(reverse=True)
    return months


def get_most_recent_month():
    """Get the latest transaction month."""
    return db_queries.get_most_recent_transaction_month()

def transaction_exists(transaction_id):
    return db_queries.transaction_exists(transaction_id) is not None