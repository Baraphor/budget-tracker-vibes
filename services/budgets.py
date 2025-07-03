import db_queries
import pandas as pd
import json


def update_budget(category_id, amount):
    """Update the budget amount for a category."""
    db_queries.update_budget_amount(category_id, amount)


def get_budget_status(month):
    """Fetch the budget status for all categories for a given month."""
    df = db_queries.get_budget_status(month)

    if df.empty:
        return []

    df = df.where(pd.notnull(df), None)
    return json.loads(df.to_json(orient='records'))

