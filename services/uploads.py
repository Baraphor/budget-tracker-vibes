import pandas as pd
import db_queries


def parse_uploaded_csv(file):
    """Parse and sanitize uploaded CSV file."""
    df = pd.read_csv(file, dtype=str, index_col=False)

    # Clean up headers
    df.columns = [col.strip() for col in df.columns]

    # Rename and filter only needed columns
    expected_columns = {
        "Account Type": "account_type",
        "Transaction Date": "transaction_date",
        "Description 1": "description1",
        "Description 2": "description2",
        "CAD$": "amount"
    }

    df = df.rename(columns=expected_columns)
    df = df[list(expected_columns.values())]

    # Convert date
    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"], format="%m/%d/%Y", errors="coerce"
    )

    return df


def choose_description(row):
    """Apply description preference logic."""
    desc1 = row.get("description1", "") or ""
    desc2 = row.get("description2", "") or ""

    if "IDP PURCHASE" in desc1:
        return desc2
    elif any(term in desc1 for term in ["MISC PAYMENT", "BILL PAYMENT", "PAYROLL DEPOSIT"]):
        return f"{desc1} {desc2}".strip()
    else:
        return desc1


def insert_unique_transactions(df):
    """Insert only new transactions, avoiding duplicates."""
    existing = db_queries.get_existing_transaction_records()

    # Merge description fields
    df["description"] = df.apply(choose_description, axis=1)
    df = df[["account_type", "transaction_date", "description", "amount"]]
    df["category"] = 1  # Default category

    if existing.empty:
        insert_count = len(df)
        df.to_sql("transactions", db_queries.get_connection(), if_exists="append", index=False)
        return insert_count

    new_df = df.merge(
        existing, on=["account_type", "transaction_date", "description", "amount"],
        how="left", indicator=True
    )
    new_df = new_df[new_df["_merge"] == "left_only"].drop(columns=["_merge"])

    insert_count = len(new_df)

    if insert_count > 0:
        new_df.to_sql("transactions", db_queries.get_connection(), if_exists="append", index=False)

    return insert_count
