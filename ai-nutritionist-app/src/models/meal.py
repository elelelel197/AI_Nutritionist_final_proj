import sqlite3 as sql
from models.user import User

class Meal:
    def __init__(self, food_items_quantity, time):
        # list of food items and quantity(in grams) in the meal
        self.food_items_quantity = food_items_quantity  # e.g., {'apple': 150, 'chicken_breast': 200} 
        self.time = time  # e.g., '2023-10-01 12:30:00'


    # Load meal from the database for a specific user and meal time
    @classmethod
    def load_meal_from_db(cls, user_id, meal_time):
        conn_user_gt = sql.connect('user_history.db')
        cursor_user_gt = conn_user_gt.cursor()
        cursor_user_gt.execute('''
            SELECT food_name, quantity FROM meals_log
            WHERE user_id = ? AND meal_time = ?
            ''', (user_id, meal_time)
            )
        meal_data = cursor_user_gt.fetchall()
        conn_user_gt.close()

        # Check if meal_data is empty
        if not meal_data:
            print(f"No meal found for user {user_id} at {meal_time}.")
            return None
        food_items_quantity = {item[0]: item[1] for item in meal_data}
        return cls(food_items_quantity, meal_time)


    # Calculate total nutritional value in the meal
    def calculate_nutritional_values(self):
        conn_food_nutrition = sql.connect('food_nutrition.db')
        cursor_food_nutrition = conn_food_nutrition.cursor()
        nutritional_values = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fats': 0
        }

        # Search database for each food item to get nutritional values then sum them up
        for food_item, quantity in self.food_items_quantity.items():
            cursor_food_nutrition.execute('''
                SELECT calories, protein, carbohydrates, fats FROM food_nutrition
                WHERE food_name = ?
                ''', (food_item,)
                )
            result = cursor_food_nutrition.fetchone()
            result = cursor_food_nutrition.fetchone()
            if result is None:
                print(f"Nutritional information for '{food_item}' not found in database.")
                return None
            nutritional_values['calories'] += (result[0] * quantity) / 100
            nutritional_values['protein'] += (result[1] * quantity) / 100
            nutritional_values['carbs'] += (result[2] * quantity) / 100
            nutritional_values['fats'] += (result[3] * quantity) / 100
        conn_food_nutrition.close()
        return nutritional_values


    # Insert the meal into the user_history database
    def log_meal_into_db(self, user_id):
        conn_user_gt = sql.connect('user_history.db')
        cursor_user_gt = conn_user_gt.cursor()
        for food_item, quantity in self.food_items_quantity.items():
            cursor_user_gt.execute('''
                INSERT INTO meals_log (user_id, food_name, quantity, meal_time)
                VALUES (?, ?, ?, ?)
                ''', (user_id, food_item, quantity, self.time)
                )
        print(f"Meal logged for user {user_id} at {self.time}.")
        conn_user_gt.commit()
        conn_user_gt.close()

    def print_meal(self):
        for food_item, quantity in self.food_items_quantity.items():
            print(f"{food_item}: {quantity}g")