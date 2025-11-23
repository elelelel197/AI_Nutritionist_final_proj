from models.user import User
import sqlite3 as sql
from typing import List, Dict, Optional, Any
import datetime

MAX_USERS = 3000

class AuthService:
    def __init__(self):
        pass


    def total_users(self):
        conn_user_history = sql.connect('user_history.db')
        cursor_user_history = conn_user_history.cursor()
        cursor_user_history.execute('''
            SELECT COUNT(*) FROM users
            ''')
        user_count = cursor_user_history.fetchone()[0]
        conn_user_history.close()
        return user_count


    def is_max_users_reached(self, max_users=MAX_USERS):
        conn_user_history = sql.connect('user_history.db')
        cursor_user_history = conn_user_history.cursor()
        cursor_user_history.execute('''
            SELECT COUNT(*) FROM users
            ''')
        user_count = cursor_user_history.fetchone()[0]
        conn_user_history.close()
        return user_count >= max_users


    def user_login(self, user_id):
        # Attempt to load user from database
        user = User.load_user_from_db(user_id)
        if user:
            print(f"User {user_id} successfully logged in.")
            return user
        else:
            print(f"Login failed for user {user_id}. User not found.")
            return None
        

    def user_register(self, id, height, weight, sex, age, estimated_time, target_weight, time):
        # Check if user already exists
        existing_user = User.load_user_from_db(id)
        if existing_user:
            print(f"User with ID {id} already exists. Registration failed.")
            return None
        # Check if max users reached
        if self.is_max_users_reached():
            print("Maximum number of users reached. Registration failed.")
            return None
        # Create new user and log to database
        new_user = User(id, height, weight, sex, age, estimated_time, target_weight)
        new_user.log_user_to_db(time)
        print(f"User {id} successfully registered.")
        return new_user
    

    def user_logout(self, user):
        print(f"User {user.id} logged out.")
        # Additional logout operations can be added here

    
    def delete_user_from_db(self, user):
        user.delete_user_from_db()
        print(f"User {user.id} deleted from database.")


    # Food table helpers
    def add_food_item(self, food_name: str, food_type: str = None,
                      calories_per_100g: float = 0, protein_per_100g: float = 0,
                      carbs_per_100g: float = 0, fats_per_100g: float = 0,
                      vitamins: str = None, minerals: str = None) -> int:
        """
        新增食物到 food_nutrition，回傳 food_id
        values are per 100g
        """
        if not food_name:
            raise ValueError("food_name 必須提供")
        conn = sql.connect("food_nutrition.db")
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO food_nutrition
                (food_name, food_type, calories, protein, carbohydrates, fats, vitamins, minerals)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (food_name, food_type, calories_per_100g, protein_per_100g,
                  carbs_per_100g, fats_per_100g, vitamins, minerals)
                  )
        return cur.lastrowid


    def get_food_by_id(self, food_id: int) -> Optional[Dict[str, Any]]:
        """取得指定 food_id 的食物資料（或 None）"""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM food_nutrition WHERE food_id = ?', (food_id,))
            row = cur.fetchone()
            return dict(row) if row else None