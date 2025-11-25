# Code has not been tested yet

import numpy as np
import sqlite3 as sql
import uuid
from models.user import User
from models.meal import Meal
import utils.nutrition_utils

ACTIVITY_LEVELS_RANDOM_DISTORTION_RANGE = (0.9, 1.1)
WEIGHT_MEASUREMENT_NOISE_STDDEV = 0.02  # 2% standard deviation
CONSUMED_FOOD_QUANTITY_NOISE_STDDEV = 0.1  # 10% standard deviation

class Simulator:
    def __init__(self, height_range=(150, 210), weight_range=(50, 200), sex_options = ["male", "female"], age_range=(15, 80), estimated_time_range=(7, 365), target_weight_range=(60, 150)):
        self.height_range =  height_range # cm
        self.weight_range =  weight_range # kg
        self.sex_options = sex_options # male/female
        self.age_range = age_range # years
        self.estimated_time_range =  estimated_time_range # days
        self.target_weight_range = target_weight_range # kg


    # Generate random UUIDs
    def create_random_id(self, amount=1):
        ids = []
        for _ in range(amount):
            ids.append(str(uuid.uuid4()))
        return ids if amount > 1 else ids[0]
    

    # Create multiple users with random attributes also with food preferences, activity levels
    def generate_user(self, amount=1):
        # Generate random UUIDs for users
        id_list = self.create_random_id(amount)

        # Connect to the user_gt and food_nutrition databases
        conn_user_gt = sql.connect('user_gt.db')
        cursor_user_gt = conn_user_gt.cursor()
        print("user_gt db connected")
        conn_food_nutrition = sql.connect('food_nutrition.db')
        cursor_food_nutrition = conn_food_nutrition.cursor()
        print("food_nutrition db connected")

        # Fetch all food types and names from food_nutrition database
        cursor_food_nutrition.execute('''
            SELECT food_type, food_name FROM food_nutrition
        ''')
        food_type_names = cursor_food_nutrition.fetchall()
        conn_food_nutrition.close()

        # Create users and insert their preferences and activity levels into the user.gt database
        new_users = [None] * amount
        for i in range(amount):
            new_users[i] = User(
                id = id_list[i],
                height = np.random.uniform(self.height_range[0], self.height_range[1]),
                weight = np.random.uniform(self.weight_range[0], self.weight_range[1]),
                sex = np.random.choice(self.sex_options),
                age = np.random.randint(self.age_range[0], self.age_range[1]),
                estimated_time = np.random.randint(self.estimated_time_range[0], self.estimated_time_range[1]),
                target_weight = np.random.uniform(self.target_weight_range[0], self.target_weight_range[1])
            )
            
            for food_tp_nm in food_type_names:
                # Every food has a random preference score between 0 and 1
                # Users have random activity levels
                cursor_user_gt.execute('''
                    INSERT INTO users_preference (user_id, food_type, food_name, food_preference)
                    VALUES (?, ?, ?, ?)
                    ''', (new_users[i].id, 
                          food_tp_nm[0], 
                          food_tp_nm[1], 
                          np.random.rand()
                          )
                    )
                cursor_user_gt.execute('''
                    INSERT INTO users_activity_level (user_id, activity_level)
                    VALUES (?, ?)
                    ''', (new_users[i].id, 
                          np.random.choice(['sedentary', 'lightly active', 'moderately active', 'very active', 'super active'])
                          )
                    )

        print(f"{amount} users created and inserted into the databases.")
        conn_user_gt.commit()   
        conn_user_gt.close()   
        return new_users if amount > 1 else new_users[0]


    # Simulate meal logging for a user based on meal recommendations
    # Returns the actual meal consumed by the user
    def simulate_meal_consumption(self, user: User, recommendation: Meal=None):
        conn_user_gt = sql.connect('user_gt.db')
        cursor_user_gt = conn_user_gt.cursor()
        food_items = recommendation.food_items_quantity.keys()
        actual_meal = Meal(recommendation.food_items_quantity, recommendation.time)
        for food in food_items:
            cursor_user_gt.execute('''
                SELECT food_type, food_preference FROM users_preference                   
                WHERE user_id = ? AND food_name = ?
                ''', (user.id, food)
                )
            result = cursor_user_gt.fetchone()
            food_type = result[0]
            food_preference = result[1]
            if np.random.rand() < food_preference:
                # User eats more of preferred food
                actual_meal.food_items_quantity[food] *= np.random.normal(loc=food_preference + 0.5, scale=CONSUMED_FOOD_QUANTITY_NOISE_STDDEV)
            else:
                # User may decide to substitute the food_item with same type of food
                # prefered food of the same type would more likely be choosen 
                # Quantity is based on recommended quantity
                cursor_user_gt.execute('''
                    SELECT food_name FROM users_preference
                    WHERE user_id = ? and food_type = ? and food_name != ?
                    ''', (user.id, food_type, food)
                    )
                food_type_preferences = cursor_user_gt.fetchall()
                prefs = [item[1] for item in food_type_preferences]
                substitution_food_with_preference = np.random.choice(food_type_preferences, p=prefs)
                substitution_food = substitution_food_with_preference[0]
                substitution_preference = substitution_food_with_preference[1]
                actual_meal.food_items_quantity[substitution_food] = actual_meal.food_items_quantity.pop(food) * np.random.normal(loc=substitution_preference + 0.5, scale=CONSUMED_FOOD_QUANTITY_NOISE_STDDEV)
        conn_user_gt.close()
        print(f"Meal logged for user {user.id}.")
        return actual_meal 


    # Simulate weight change over a period based on caloric intake and activity level
    def simulate_weight_change(self, user: User, days_passed: int, total_caloric_intake: float):
        conn_user_gt = sql.connect('user_gt.db')
        cursor_user_gt = conn_user_gt.cursor()
        cursor_user_gt.execute('''
            SELECT * from users_activity_level                   
            WHERE user_id = ?
            ''', (user.id,)
            )
        user_activity_level = cursor_user_gt.fetchone()[1]
        conn_user_gt.close()

        # Users have different activity levels on different days but stays within a range of their average activity level
        # Sampling N times and averaging: The average’s variability decreases as N increases (by Central Limit Theorem)
        daily_distortions = np.random.uniform(ACTIVITY_LEVELS_RANDOM_DISTORTION_RANGE[0], ACTIVITY_LEVELS_RANDOM_DISTORTION_RANGE[1], days_passed)
        activity_level_random_distortion = np.mean(daily_distortions)
        if(user_activity_level == 'sedentary' and activity_level_random_distortion < 1):
            activity_level_random_distortion = 1
        elif(user_activity_level == 'super active' & activity_level_random_distortion > 1):
            activity_level_random_distortion = 1
        daily_caloric_needs = utils.nutrition_utils.calculate_daily_caloric_needs(
            weight=user.weight,
            height=user.height,
            age=user.age,
            sex=user.sex,
            activity_level=user_activity_level
        ) * activity_level_random_distortion
        total_caloric_gain_loss = total_caloric_intake - (daily_caloric_needs * days_passed)
        weight_change = utils.nutrition_utils.calculate_caloric_gain_loss_to_weight_change(total_caloric_gain_loss)
        # weight could be affected by random factors like water retention, measurement noise, etc.
        weight_measure_random_distortion = np.random.normal(loc=1.0, scale=WEIGHT_MEASUREMENT_NOISE_STDDEV)  # mean=1.0, std=0.02
        new_weight = (user.weight + weight_change) * weight_measure_random_distortion

        print(f"User {user.id} weight changed from {user.weight:.2f} kg to {new_weight:.2f} kg over {days_passed} days.")
        return new_weight

     