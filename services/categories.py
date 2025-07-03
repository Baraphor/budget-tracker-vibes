import pandas as pd
import db_queries


def get_categories():
    """Fetch all categories as a list of dictionaries."""
    df = db_queries.get_all_categories()
    
    categories = []
    for _, row in df.iterrows():
        parent_id = None if pd.isna(row["parent_id"]) else int(row["parent_id"])
        
        categories.append({
            "id": int(row["id"]),
            "name": row["name"],
            "parent_id": parent_id,
            "include_in_budget": row["include_in_budget"]
        })
    
    return categories

def get_categories_with_subcategories():
    df = db_queries.get_all_categories()  # Returns a DataFrame

    categories = []
    id_to_cat = {}

    # Iterate over DataFrame rows
    for _, row in df.iterrows():
        cat = {
            "id": row["id"],
            "name": row["name"],
            "parent_id": row["parent_id"],
            "subcategories": []
        }
        id_to_cat[cat["id"]] = cat
        if pd.isna(cat["parent_id"]):
            categories.append(cat)

    for _, row in df.iterrows():
        if not pd.isna(row["parent_id"]):
            parent = id_to_cat.get(row["parent_id"])
            if parent:
                child = {
                    "id": row["id"],
                    "name": row["name"],
                    "parent_id": row["parent_id"]
                }
                parent["subcategories"].append(child)

    return categories



def add_category(name, parent_id=None):
    """Add a new category."""
    db_queries.insert_category(name, parent_id)


def delete_category(category_id):
    """Delete a category by ID."""
    db_queries.delete_category(category_id)


def update_category_name(category_id, new_name):
    """Rename a category."""
    db_queries.update_category_name(category_id, new_name)
    

def toggle_include_in_budget(category_id):
    db_queries.toggle_include_in_budget(category_id)

def category_exists(category_id):
    return db_queries.get_category(category_id) is not None