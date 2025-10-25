from datetime import datetime
import sqlite3

class MealTracker:
    def __init__(self, db_path):
        self.db_path = db_path

    def log_meal(self, user_id, meal_details):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_history (user_id, meal_details, date)
            VALUES (?, ?, ?)
        ''', (user_id, meal_details, datetime.now()))
        conn.commit()
        conn.close()

    def get_meal_history(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT meal_details, date FROM user_history
            WHERE user_id = ?
            ORDER BY date DESC
        ''', (user_id,))
        meals = cursor.fetchall()
        conn.close()
        return meals

    def get_current_weight(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT weight FROM user_history
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT 1
        ''', (user_id,))
        weight = cursor.fetchone()
        conn.close()
        return weight[0] if weight else None

    def update_weight(self, user_id, new_weight):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_history (user_id, weight, date)
            VALUES (?, ?, ?)
        ''', (user_id, new_weight, datetime.now()))
        conn.commit()
        conn.close()