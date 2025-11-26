import sqlite3
import os

def drop_all_tables(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table[0]};")
        print(f"Dropped table: {table[0]}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    base_dir = os.path.join(os.path.dirname(__file__), "database")
    db_files = [
        "user_history.db",
        "user_pred.db",
        "user_gt.db",
        "food_nutrition.db"
    ]
    for db_name in db_files:
        db_path = os.path.join(base_dir, db_name)
        if os.path.exists(db_path):
            drop_all_tables(db_path)