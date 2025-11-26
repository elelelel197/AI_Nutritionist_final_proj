import sqlite3 as sql
from models.user import User
import utils.file_paths as fp

class Meal:
    def __init__(self, food_items_quantity, time):
        # list of food items and quantity(in grams) in the meal
        self.food_items_quantity = food_items_quantity  # e.g., {'apple': 150, 'chicken_breast': 200} 
        self.time = time  # e.g., '2023-10-01 12:30:00'


    # Load meal from the database for a specific user and meal time
    @classmethod
    def load_meal_from_db(cls, user_id, meal_time):
        conn_user_gt = sql.connect(fp.get_user_history_db_path())
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
        conn_food_nutrition = sql.connect(fp.get_food_nutrition_db_path())
        cursor_food_nutrition = conn_food_nutrition.cursor()
        nutritional_values = {
            'calories': 0,
            'protein': 0,
            'carbohydrates': 0,
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
            
            if result is None:
                print(f"Nutritional information for '{food_item}' not found in database.")
                return None
            nutritional_values['calories'] += (result[0] * quantity) / 100
            nutritional_values['protein'] += (result[1] * quantity) / 100
            nutritional_values['carbohydrates'] += (result[2] * quantity) / 100
            nutritional_values['fats'] += (result[3] * quantity) / 100
        conn_food_nutrition.close()
        return nutritional_values


    # Insert the meal into the user_history database
    def log_meal_into_db(self, user_id, recommend_or_actual='actual'):
        conn_user_gt = sql.connect(fp.get_user_history_db_path())
        cursor_user_gt = conn_user_gt.cursor()
        for food_item, quantity in self.food_items_quantity.items():
            if (recommend_or_actual == 'recommended'):
                cursor_user_gt.execute('''
                    INSERT INTO recommend_meals_log (user_id, food_name, quantity, meal_time)
                    VALUES (?, ?, ?, ?)
                    ''', (user_id, food_item, quantity, self.time)
                    )
            else:
                cursor_user_gt.execute('''
                    INSERT INTO meals_log (user_id, food_name, quantity, meal_time)
                    VALUES (?, ?, ?, ?)
                    ''', (user_id, food_item, quantity, self.time)
                    )
        print(f"{recommend_or_actual} Meal logged for user {user_id} at {self.time}.")
        conn_user_gt.commit()
        conn_user_gt.close()


    def get_food_type(self):
        conn_food_nutrition = sql.connect(fp.get_food_nutrition_db_path())
        cursor_food_nutrition = conn_food_nutrition.cursor()
        food_type = []
        for food_item in self.food_items_quantity.keys():
            cursor_food_nutrition.execute('''
                SELECT food_type FROM food_nutrition
                WHERE food_name = ?
                ''', (food_item,)
                )
            result = cursor_food_nutrition.fetchone()
            if result:
                food_type.append(result[0])
        conn_food_nutrition.close()
        return food_type


    def print_meal(self):
        for food_item, quantity in self.food_items_quantity.items():
            print(f"{food_item}: {quantity}g")


    # Food table helpers
    @staticmethod
    def add_food_item(food_name: str, food_type: str = None,
                      calories_per_100g: float = 0, protein_per_100g: float = 0,
                      carbohydrates_per_100g: float = 0, fats_per_100g: float = 0,
                      vitamins: str = None, minerals: str = None) -> int:
        """
        新增食物到 food_nutrition，回傳 food_id
        values are per 100g
        """
        if not food_name:
            raise ValueError("food_name 必須提供")
        conn = sql.connect(fp.get_food_nutrition_db_path())
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO food_nutrition
                (food_type, food_name, calories, protein, carbohydrates, fats, vitamins, minerals)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (food_type, food_name, calories_per_100g, protein_per_100g,
                  carbohydrates_per_100g, fats_per_100g, vitamins, minerals)
                  )
        conn.commit()
        conn.close()
        return cur.lastrowid


    @staticmethod
    def get_food_type_by_name(food_name: str) :
        """
        由 food_name 查詢 food_type
        """
        conn = sql.connect(fp.get_food_nutrition_db_path())
        cur = conn.cursor()
        cur.execute('''
            SELECT food_type FROM food_nutrition
            WHERE food_name = ?
            ''', (food_name,)
            )
        result = cur.fetchone()
        conn.close()
        if result:
            return result[0]
        return None
    
    @staticmethod
    def get_food_nutrition_by_name(food_name: str):
        """
        由 food_name 查詢 食物營養成分
        """
        conn = sql.connect(fp.get_food_nutrition_db_path())
        cur = conn.cursor()
        cur.execute('''
            SELECT calories, protein, carbohydrates, fats FROM food_nutrition
            WHERE food_name = ?
            ''', (food_name,)
            )
        result = cur.fetchone()
        conn.close()
        if result:
            return {
                'calories': result[0],
                'protein': result[1],
                'carbohydrates': result[2],
                'fats': result[3]
            }
        return None