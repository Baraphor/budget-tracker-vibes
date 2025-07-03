from flask import Flask, jsonify, request, render_template, g
from functools import wraps
import storage
import secrets
import time
import validation
from datetime import datetime
import services.transactions as transactions_service
import services.categories as categories_service
import services.budgets as budgets_service
import services.graphs as graphs_service
import services.uploads as uploads_service
import services.setup as setup_service
import logging
import sys
import os

# --- Flask App Setup ---
app = Flask(__name__)
setup_service.initialize_database()
os.makedirs('logs', exist_ok=True)
log_file = 'logs/app.log'
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# ---------------- Session Token Helpers ----------------

def require_session_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Session-Token")
        if not token:
            app.logger.warning("Missing session token")
            return jsonify({"error": "Missing session token"}), 403

        validation_result = storage.validate_and_track_token(token)

        if validation_result == "expired":
            app.logger.warning("Session token expired")
            return jsonify({"error": "Session token expired"}), 403
        elif validation_result == "invalid":
            app.logger.warning("Invalid session token")
            return jsonify({"error": "Invalid session token"}), 403
        elif validation_result == "rate_limit":
            app.logger.warning("Rate limit exceeded")
            return jsonify({"error": "Rate limit exceeded"}), 429

        return f(*args, **kwargs)
    return decorated

def get_or_create_session_token():
    ip_address = request.remote_addr
    token = storage.get_active_token_for_ip(ip_address)
    if not token:
        token = storage.create_session_token(ip_address)
        app.logger.info(f"Session token created for IP {ip_address}")
    g.session_token = token

# ---------------- Index & Pages ----------------

@app.route("/")
@app.route("/index")
def index():
    get_or_create_session_token()
    app.logger.info("Index page accessed")
    categories = categories_service.get_categories_with_subcategories()
    return render_template("index.html", categories=categories, session_token=g.session_token)

@app.route("/categories")
def categories():
    get_or_create_session_token()
    app.logger.info("Categories page accessed")
    categories = categories_service.get_categories()
    return render_template("categories.html", categories=categories, session_token=g.session_token)

@app.route("/graphs")
def graphs():
    get_or_create_session_token()
    app.logger.info("Graphs page accessed")
    months = graphs_service.get_available_months()
    return render_template("graphs.html", months=months, session_token=g.session_token)

@app.route("/budget")
def budget():
    get_or_create_session_token()
    app.logger.info("Budget page accessed")
    month = transactions_service.get_most_recent_month()
    categories = budgets_service.get_budget_status(month)
    months = transactions_service.get_transaction_months()
    return render_template("budget.html", categories=categories, month=month, months=months, session_token=g.session_token)

# ---------------- Transactions ----------------

@app.route("/transactions/get")
@require_session_token
def get_transactions():
    df = transactions_service.get_transactions()
    app.logger.info("Transactions retrieved")
    return df.to_json(orient="records")

@app.route("/transaction/update/category", methods=["POST"])
@require_session_token
def assign_category():
    data = request.get_json()
    transaction_id = data.get("transaction_id")
    category_id = data.get("category_id")

    if not validation.validate_positive_int(transaction_id) or not validation.validate_positive_int(category_id):
        app.logger.warning("Invalid transaction or category ID")
        return jsonify({"success": False, "error": "Invalid transaction or category ID"}), 400

    if not transactions_service.transaction_exists(transaction_id):
        app.logger.warning(f"Transaction {transaction_id} does not exist")
        return jsonify({"success": False, "error": "Transaction does not exist"}), 404

    if not categories_service.category_exists(category_id):
        app.logger.warning(f"Category {category_id} does not exist")
        return jsonify({"success": False, "error": "Category does not exist"}), 404

    transactions_service.update_transaction_category(transaction_id, category_id)
    app.logger.info(f"Transaction {transaction_id} category updated to {category_id}")
    return "", 204

@app.route("/transaction/update/description", methods=["POST"])
@require_session_token
def update_description():
    data = request.get_json()
    transaction_id = data.get("id")
    description = data.get("description")

    if not validation.validate_positive_int(transaction_id) or not validation.sanitize_string(description, 500):
        app.logger.warning("Invalid transaction ID or description")
        return jsonify({"success": False, "error": "Invalid input"}), 400

    if not transactions_service.transaction_exists(transaction_id):
        app.logger.warning(f"Transaction {transaction_id} does not exist")
        return jsonify({"success": False, "error": "Transaction does not exist"}), 404

    transactions_service.update_transaction_description(transaction_id, description)
    app.logger.info(f"Transaction {transaction_id} description updated")
    return "", 204

@app.route("/transaction/add", methods=["POST"])
@require_session_token
def add_transaction():
    data = request.get_json()
    amount = data.get("amount")
    description = data.get("description")
    transaction_date = data.get("transaction_date")
    account_type = data.get("account_type")
    category = data.get("category")

    if not validation.validate_number(amount):
        app.logger.warning("Invalid amount")
        return jsonify({"success": False, "error": "Invalid amount"}), 400

    if not validation.sanitize_string(description, 500):
        app.logger.warning("Invalid description")
        return jsonify({"success": False, "error": "Invalid description"}), 400

    try:
        datetime.strptime(transaction_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        app.logger.warning("Invalid transaction date format")
        return jsonify({"success": False, "error": "Invalid transaction date"}), 400

    if not validation.sanitize_string(account_type, 100):
        app.logger.warning("Invalid account type")
        return jsonify({"success": False, "error": "Invalid account type"}), 400

    if category is not None and not validation.validate_id(category):
        app.logger.warning("Invalid category ID")
        return jsonify({"success": False, "error": "Invalid category"}), 400

    new_id = transactions_service.add_transaction(data)
    transaction = transactions_service.get_transaction(new_id)
    app.logger.info(f"Transaction added with ID {new_id}")
    return jsonify(transaction)

@app.route("/transaction/delete/<int:transaction_id>", methods=["DELETE"])
@require_session_token
def delete_transaction(transaction_id):
    if not transactions_service.transaction_exists(transaction_id):
        app.logger.warning(f"Transaction {transaction_id} does not exist")
        return jsonify({"success": False, "error": "Transaction does not exist"}), 404

    transactions_service.delete_transaction(transaction_id)
    app.logger.info(f"Transaction {transaction_id} deleted")
    return "", 204

@app.route("/settings/clear-transactions", methods=["DELETE"])
@require_session_token
def clear_transactions():
    transactions_service.clear_all_transactions()
    app.logger.info("All transactions cleared")
    return "", 204

@app.route("/transactions/get/months", methods=["GET"])
@require_session_token
def get_transaction_months():
    months = transactions_service.get_transaction_months()
    app.logger.info("Transaction months retrieved")
    return jsonify(months)

# ---------------- Categories ----------------

@app.route("/categories/add", methods=["POST"])
@require_session_token
def add_category():
    data = request.get_json()
    name = data.get("name")
    parent_id = data.get("parent_id")

    if not validation.sanitize_string(name):
        app.logger.warning("Invalid category name")
        return jsonify({"success": False, "error": "Invalid category name"}), 400

    if parent_id is not None and not validation.validate_positive_int(parent_id):
        app.logger.warning("Invalid parent category ID")
        return jsonify({"success": False, "error": "Invalid parent ID"}), 400

    if parent_id and not categories_service.category_exists(parent_id):
        app.logger.warning(f"Parent category {parent_id} does not exist")
        return jsonify({"success": False, "error": "Parent category does not exist"}), 404

    categories_service.add_category(name, parent_id)
    app.logger.info(f"Category '{name}' added with parent {parent_id}")
    return "", 204

@app.route("/categories/delete/<int:category_id>", methods=["DELETE"])
@require_session_token
def delete_category(category_id):
    if not categories_service.category_exists(category_id):
        app.logger.warning(f"Category {category_id} does not exist")
        return jsonify({"success": False, "error": "Category does not exist"}), 404

    categories_service.delete_category(category_id)
    app.logger.info(f"Category {category_id} deleted")
    return "", 204

@app.route("/categories/update", methods=["POST"])
@require_session_token
def update_category():
    data = request.get_json()
    category_id = data.get("id")
    new_name = data.get("new_name")

    if not validation.validate_positive_int(category_id) or not validation.sanitize_string(new_name):
        app.logger.warning("Invalid category ID or name")
        return jsonify({"success": False, "error": "Invalid input"}), 400

    if not categories_service.category_exists(category_id):
        app.logger.warning(f"Category {category_id} does not exist")
        return jsonify({"success": False, "error": "Category does not exist"}), 404

    categories_service.update_category_name(category_id, new_name)
    app.logger.info(f"Category {category_id} renamed to '{new_name}'")
    return "", 204

@app.route("/categories/toggle_include/<int:category_id>", methods=["POST"])
@require_session_token
def toggle_include_in_budget(category_id):
    if not categories_service.category_exists(category_id):
        app.logger.warning(f"Category {category_id} does not exist")
        return jsonify({"success": False, "error": "Category does not exist"}), 404

    categories_service.toggle_include_in_budget(category_id)
    app.logger.info(f"Category {category_id} include_in_budget toggled")
    return "", 204

# ---------------- Budgets ----------------

@app.route("/budget/update", methods=["POST"])
@require_session_token
def update_budget():
    data = request.get_json()
    category_id = data.get("category_id")
    amount = data.get("amount")

    if not validation.validate_positive_int(category_id) or not validation.validate_number(amount):
        app.logger.warning("Invalid budget input")
        return jsonify({"success": False, "error": "Invalid input"}), 400

    if not categories_service.category_exists(category_id):
        app.logger.warning(f"Category {category_id} does not exist")
        return jsonify({"success": False, "error": "Category does not exist"}), 404

    budgets_service.update_budget(category_id, amount)
    app.logger.info(f"Budget for category {category_id} updated to {amount}")
    return "", 204

# ---------------- Graphs & Summaries ----------------

@app.route("/graphs/get/monthly", methods=["POST"])
@require_session_token
def get_graph_data():
    data = request.get_json()
    month_filter = data.get("month")

    if month_filter and not validation.sanitize_string(month_filter, 10):
        app.logger.warning("Invalid month filter")
        return jsonify({"success": False, "error": "Invalid month filter"}), 400

    graph_data = graphs_service.get_graph_data(month_filter)
    app.logger.info("Graph data retrieved")
    return jsonify(graph_data)

@app.route("/graphs/get/summary")
@require_session_token
def get_income_expense():
    summary = graphs_service.get_income_expense_summary()
    app.logger.info("Income/expense summary retrieved")
    return jsonify(summary)

# ---------------- Uploads ----------------

@app.route("/upload", methods=["POST"])
@require_session_token
def upload():
    try:
        file = request.files.get("file")
        if not file:
            app.logger.warning("No file uploaded")
            return jsonify({"success": False, "error": "No file uploaded"}), 400

        if not file.filename.endswith(".csv"):
            app.logger.warning("Invalid file type")
            return jsonify({"success": False, "error": "Invalid file type"}), 400

        contents = file.read().decode("utf-8", errors="ignore")
        rows = contents.splitlines()

        header = rows[0].split(",")
        expected_columns = ["Account Type", "Account Number", "Transaction Date", "Cheque Number", "Description 1", "Description 2", "CAD$", "USD$"]

        if header != expected_columns:
            app.logger.warning("CSV header mismatch")
            return jsonify({"success": False, "error": "Invalid CSV format"}), 400

        for line in rows[1:]:
            fields = line.split(",")
            if len(fields) != len(expected_columns):
                app.logger.warning("Malformed CSV row detected")
                return jsonify({"success": False, "error": "Malformed CSV data"}), 400

            if not validation.validate_date(fields[2]) or not validation.validate_number(fields[-1]):
                app.logger.warning("Invalid data in CSV row")
                return jsonify({"success": False, "error": "Invalid data in CSV"}), 400

        app.logger.info("CSV file validated and ready for processing")
        return jsonify({"success": True})

    except Exception as e:
        app.logger.error(f"Error processing CSV: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Internal server error"}), 500

# ---------------- Settings ----------------

@app.route("/settings")
def settings():
    get_or_create_session_token()
    app.logger.info("Settings page accessed")
    return render_template("settings.html", session_token=g.session_token)

# ---------------- Jinja Helpers ----------------

def has_children(categories, parent_id):
    return any(c['parent_id'] == parent_id for c in categories)

app.jinja_env.globals.update(has_children=has_children)

# ---------------- Run ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
