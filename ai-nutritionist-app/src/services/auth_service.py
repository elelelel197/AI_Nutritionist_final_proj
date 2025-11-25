from models.user import User
import sqlite3 as sql
from typing import List, Dict, Optional, Any
import datetime

MAX_USERS = 3000

class AuthService:
    def __init__(self):
        pass


    @staticmethod
    def total_users():
        conn_user_history = sql.connect('user_history.db')
        cursor_user_history = conn_user_history.cursor()
        cursor_user_history.execute('''
            SELECT COUNT(*) FROM users
            ''')
        user_count = cursor_user_history.fetchone()[0]
        conn_user_history.close()
        return user_count


    @staticmethod
    def is_max_users_reached(max_users=MAX_USERS):
        conn_user_history = sql.connect('user_history.db')
        cursor_user_history = conn_user_history.cursor()
        cursor_user_history.execute('''
            SELECT COUNT(*) FROM users
            ''')
        user_count = cursor_user_history.fetchone()[0]
        conn_user_history.close()
        return user_count >= max_users


    @staticmethod
    def user_login(user_id):
        # Attempt to load user from database
        user = User.load_user_from_db(user_id)
        if user:
            print(f"User {user_id} successfully logged in.")
            return user
        else:
            print(f"Login failed for user {user_id}. User not found.")
            return None
        

    @staticmethod
    def user_register(id, height, weight, sex, age, estimated_time, target_weight, time):
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
    

    @staticmethod
    def user_logout(user):
        print(f"User {user.id} logged out.")
        # Additional logout operations can be added here

    @staticmethod
    def delete_user_from_db(user):
        user.delete_user_from_db()
        print(f"User {user.id} deleted from database.")


    