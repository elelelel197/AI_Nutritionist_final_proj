import sqlite3
import os

def initialize_db(db_path, sql_path):
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(sql_script)
        print(f"Initialized {db_path} from {sql_path}")
    except Exception as e:
        print(f"Error initializing {db_path}: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_sql_pairs = [
        ("user_history.db", "user_history.sql"),
        ("user_pred.db", "user_pred.sql"),
        ("user_gt.db", "user_gt.sql"),
        ("food_nutrition.db", "food_nutrition.sql"),
    ]
    for db_name, sql_name in db_sql_pairs:
        db_path = os.path.join(base_dir, "database", db_name)
        sql_path = os.path.join(base_dir, "database", sql_name)
        initialize_db(db_path, sql_path)