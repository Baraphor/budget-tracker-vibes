import db_queries
import pandas as pd


def get_graph_data(month_filter=None):
    """Prepare graph data with category and subcategory breakdowns."""
    df = db_queries.get_graph_data_for_month()

    if df.empty:
        return {
            "months": [],
            "category_totals": {},
            "subcategory_totals": {}
        }

    df["amount"] = abs(pd.to_numeric(df["amount"], errors="coerce"))

    df["month"] = pd.to_datetime(df["transaction_date"]).dt.strftime("%Y-%m")
    months = sorted(df["month"].unique(), reverse=True)

    if month_filter and month_filter != "all" and month_filter in df["month"].values:
        df = df[df["month"] == month_filter]

    df["top_category"] = df.apply(
        lambda row: row["parent_name"] if pd.notna(row["parent_name"]) else row["category_name"], axis=1
    )

    category_totals = df.groupby("top_category")["amount"].sum().round(2).to_dict()

    subcategory_totals = {}
    for top_cat, group in df.groupby("top_category"):
        sub_breakdown = group.groupby("category_name")["amount"].sum().round(2).to_dict()
        subcategory_totals[top_cat] = sub_breakdown

    return {
        "months": months,
        "category_totals": category_totals,
        "subcategory_totals": subcategory_totals
    }


def get_available_months():
    """Return available transaction months for filtering."""
    df = db_queries.get_available_months()
    if df.empty:
        return []
    df["month"] = pd.to_datetime(df["transaction_date"]).dt.strftime("%Y-%m")
    return sorted(df["month"].unique(), reverse=True)


def get_income_expense_summary():
    """Return income and expense totals by month."""
    df = db_queries.get_income_expense_by_month()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    if df.empty:
        return []

    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df = df.dropna(subset=["transaction_date"])
    df["year_month"] = df["transaction_date"].dt.to_period("M")

    summary = df.groupby("year_month").apply(
        lambda x: pd.Series({
            "income": x.loc[x["amount"] > 0, "amount"].sum(),
            "expenses": x.loc[x["amount"] < 0, "amount"].sum()
        }),
        include_groups=False
    ).reset_index()

    summary["month"] = summary["year_month"].astype(str)
    return summary[["month", "income", "expenses"]].tail(12).to_dict(orient="records")
