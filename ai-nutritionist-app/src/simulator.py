from datetime import date, timedelta
from unittest import result
import numpy as np
import sqlite3 as sql
import uuid
import csv
import pandas as pd
from models.user import User
from models.meal import Meal
from utils.nutrition_utils import NutritionUtils
import utils.file_paths as fp
from services.recommendation_service import RecommendationService
from algorithms.preference_algo import PreferenceAlgo
from algorithms.activity_lv_algo import ActivityLvAlgo
from algorithms.weight_g_l_algo import WeightGLAlgo

ACTIVITY_LEVELS_RANDOM_DISTORTION_RANGE = (0.9, 1.1)
WEIGHT_MEASUREMENT_NOISE_STDDEV = 0.02  # 2% standard deviation
CONSUMED_FOOD_QUANTITY_NOISE_STDDEV = 0.1  # 10% standard deviation

class Simulator:
    def __init__(self, height_range=(150, 210), weight_range=(50, 200), sex_options = ["M", "F"], age_range=(15, 80), estimated_days_range=(7, 365), target_weight_range=(60, 150)):
        self.height_range =  height_range # cm
        self.weight_range =  weight_range # kg
        self.sex_options = sex_options # male/female
        self.age_range = age_range # years
        self.estimated_days_range =  estimated_days_range # days
        self.target_weight_range = target_weight_range # kg


    # Generate random UUIDs
    def create_random_id(self, amount=1):
        ids = []
        for _ in range(amount):
            ids.append(str(uuid.uuid4()))
        return ids if amount > 1 else ids[0]
    

    # Create multiple users with random attributes also with food preferences, activity levels
    def generate_user(self, amount=1) -> list[User] | User:
        # Generate random UUIDs for users
        id_list = self.create_random_id(amount)

        # Connect to the user_gt and food_nutrition databases
        conn_user_gt = sql.connect(fp.get_user_gt_db_path())
        cursor_user_gt = conn_user_gt.cursor()
        print("user_gt db connected")
        conn_food_nutrition = sql.connect(fp.get_food_nutrition_db_path())
        cursor_food_nutrition = conn_food_nutrition.cursor()
        print("food_nutrition db connected")

        # Fetch all food types and names from food_nutrition database
        cursor_food_nutrition.execute('''
            SELECT food_type, food_name FROM food_nutrition
        ''')
        food_type_names = cursor_food_nutrition.fetchall()
        conn_food_nutrition.close()

        # Create users and insert their preferences and activity levels into the user.gt database
        new_users = []
        for i in range(amount):
            new_users.append(
                User(
                    id = id_list[i],
                    height = np.random.uniform(self.height_range[0], self.height_range[1]),
                    weight = np.random.uniform(self.weight_range[0], self.weight_range[1]),
                    sex = np.random.choice(self.sex_options),
                    age = np.random.randint(self.age_range[0], self.age_range[1]),
                    estimated_days = np.random.randint(self.estimated_days_range[0], self.estimated_days_range[1]),
                    target_weight = np.random.uniform(self.target_weight_range[0], self.target_weight_range[1])
                )
            )
            
            for food_tp_nm in food_type_names:
                # Every food has a random preference score between 0 and 1
                cursor_user_gt.execute('''
                    INSERT INTO users_preference (user_id, food_type, food_name, food_preference)
                    VALUES (?, ?, ?, ?)
                    ''', (new_users[i].id, 
                          food_tp_nm[0], 
                          food_tp_nm[1], 
                          np.random.rand()
                          )
                    )
                
            # Users have random activity levels
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
        conn_user_gt = sql.connect(fp.get_user_gt_db_path())
        cursor_user_gt = conn_user_gt.cursor()
        food_items = list(recommendation.food_items_quantity.keys())
        actual_meal = Meal(recommendation.food_items_quantity.copy(), recommendation.time)
        for food in food_items:
            cursor_user_gt.execute('''
                SELECT food_type, food_preference FROM users_preference                   
                WHERE user_id = ? AND food_name = ?
                ''', (user.id, food)
            )
            result = cursor_user_gt.fetchone() 
            food_type = result[0] if result else 'nan'
            food_preference = result[1] if result else 0.5
            if np.random.rand() < food_preference:
                # User eats more of preferred food
                actual_meal.food_items_quantity[food] *= np.random.normal(loc=food_preference + 0.5, scale=CONSUMED_FOOD_QUANTITY_NOISE_STDDEV)
            else:
                # User may decide to substitute the food_item with same type of food
                # prefered food of the same type would more likely be choosen 
                # Quantity is based on recommended quantity
                cursor_user_gt.execute('''
                    SELECT food_name, food_preference FROM users_preference
                    WHERE user_id = ? and food_type = ? and food_name != ?
                    ''', (user.id, food_type, food)
                    )
                food_type_preferences = cursor_user_gt.fetchall()
                prefs = np.array([item[1] for item in food_type_preferences])
                prefs = prefs / prefs.sum() if prefs.sum() > 0 else np.ones_like(prefs) / len(prefs)
                idx = np.random.choice(len(food_type_preferences), p=prefs)
                substitution_food = food_type_preferences[idx][0]
                substitution_preference = food_type_preferences[idx][1]
                actual_meal.food_items_quantity[substitution_food] = actual_meal.food_items_quantity.pop(food) * np.random.normal(loc=substitution_preference + 0.5, scale=CONSUMED_FOOD_QUANTITY_NOISE_STDDEV)
        conn_user_gt.close()
        return actual_meal 


    # Simulate weight change over a period based on caloric intake and activity level
    def simulate_weight_change(self, user: User, days_passed: int, total_caloric_intake: float):
        conn_user_gt = sql.connect(fp.get_user_gt_db_path())
        cursor_user_gt = conn_user_gt.cursor()
        cursor_user_gt.execute('''
            SELECT * from users_activity_level                   
            WHERE user_id = ?
            ''', (user.id,)
            )
        result = cursor_user_gt.fetchone()
        user_activity_level = result[1] if result else 'moderately active'
        conn_user_gt.close()

        # Users have different activity levels on different days but stays within a range of their average activity level
        # Sampling N times and averaging: The average’s variability decreases as N increases (by Central Limit Theorem)
        daily_distortions = np.random.uniform(ACTIVITY_LEVELS_RANDOM_DISTORTION_RANGE[0], ACTIVITY_LEVELS_RANDOM_DISTORTION_RANGE[1], days_passed)
        activity_level_random_distortion = np.mean(daily_distortions)
        if(user_activity_level == 'sedentary' and activity_level_random_distortion < 1):
            activity_level_random_distortion = 1
        elif(user_activity_level == 'super active' and activity_level_random_distortion > 1):
            activity_level_random_distortion = 1
        daily_caloric_needs = NutritionUtils.calculate_daily_caloric_needs(
            weight=user.weight,
            height=user.height,
            age=user.age,
            sex=user.sex,
            activity_level=user_activity_level
        ) * activity_level_random_distortion
        total_caloric_gain_loss = total_caloric_intake - (daily_caloric_needs * days_passed)
        weight_change = NutritionUtils.calculate_caloric_gain_loss_to_weight_change(total_caloric_gain_loss)
        # weight could be affected by random factors like water retention, measurement noise, etc.
        weight_measure_random_distortion = np.random.normal(loc=1.0, scale=WEIGHT_MEASUREMENT_NOISE_STDDEV)  # mean=1.0, std=0.02
        new_weight = (user.weight + weight_change) * weight_measure_random_distortion

        print(f"User {user.id} weight changed from {user.weight:.2f} kg to {new_weight:.2f} kg over {days_passed} days.")
        return new_weight



if __name__ == "__main__":
    simulator = Simulator()
    users = simulator.generate_user(amount=5)
    user_info_results = []
    meal_results = []
    comparison_results = []

    for user in users:
        user.log_user_to_db(time=date.today())
        user_info_results.append({
            "user_id": user.id,
            "height": round(user.height, 2),
            "weight": round(user.weight, 2),
            "sex": user.sex,
            "age": user.age,
            "estimated_days": user.estimated_days,
            "target_weight": round(user.target_weight, 2)
        })
        print(f"User ID: {user.id}, Height: {user.height:.2f} cm, Weight: {user.weight:.2f} kg")

    for day in range(30):
        time = date.today() + timedelta(days=day)
        for user in users:
            recommended_meal = RecommendationService.get_meal_recommendations(user, time)
            recommended_meal.log_meal_into_db(user.id, 'recommended')
            actual_meal = simulator.simulate_meal_consumption(user, recommended_meal)
            actual_meal.log_meal_into_db(user.id, 'actual')
            food_name_list = pd.Series(list(actual_meal.food_items_quantity.keys())).unique()
            preference_model = PreferenceAlgo.train_or_update_model()
            for food in food_name_list:
                preference_score = PreferenceAlgo.predict_preference(
                    preference_model, user.id, food, 0, actual_meal.food_items_quantity[food], food_name_list)
            new_weight = simulator.simulate_weight_change(user, days_passed=1, total_caloric_intake=actual_meal.calculate_nutritional_values()['calories'])
            user.update_weight(new_weight, time)
            X, y, activity_categories = ActivityLvAlgo.fetch_activity_data()
            activity_model = ActivityLvAlgo.train_or_update_model(X, y)
            predicted_level = ActivityLvAlgo.predict_activity_level(activity_model, user, activity_categories)
            factors = WeightGLAlgo.update_weight_gain_loss_factor(user)

            # --- Collect user_pred and user_gt info ---
            # Connect to both databases
            conn_pred = sql.connect(fp.get_user_pred_db_path())
            conn_gt = sql.connect(fp.get_user_gt_db_path())
            cursor_pred = conn_pred.cursor()
            cursor_gt = conn_gt.cursor()

            # Food preference: collect as a string for each user
            cursor_pred.execute("SELECT food_name, food_preference FROM users_preference WHERE user_id = ?", (user.id,))
            pred_prefs = "; ".join([f"{row[0]}:{row[1]:.2f}" for row in cursor_pred.fetchall()])
            cursor_gt.execute("SELECT food_name, food_preference FROM users_preference WHERE user_id = ?", (user.id,))
            gt_prefs = "; ".join([f"{row[0]}:{row[1]:.2f}" for row in cursor_gt.fetchall()])

            # Activity level
            cursor_pred.execute("SELECT activity_level FROM users_activity_level WHERE user_id = ?", (user.id,))
            pred_act = cursor_pred.fetchone()
            pred_act = pred_act[0] if pred_act else ""
            cursor_gt.execute("SELECT activity_level FROM users_activity_level WHERE user_id = ?", (user.id,))
            gt_act = cursor_gt.fetchone()
            gt_act = gt_act[0] if gt_act else ""

            # Weight gain/loss factor
            cursor_pred.execute("SELECT weight_gain_factor, weight_loss_factor FROM user_weight_gain_loss_factor WHERE user_id = ?", (user.id,))
            pred_wgl = cursor_pred.fetchone()
            pred_gain = pred_wgl[0] if pred_wgl else ""
            pred_loss = pred_wgl[1] if pred_wgl else ""
            

            comparison_results.append({
                "day": day + 1,
                "user_id": user.id,
                "date": time.strftime("%Y-%m-%d"),
                "pred_food_preference": pred_prefs,
                "gt_food_preference": gt_prefs,
                "pred_activity_level": pred_act,
                "gt_activity_level": gt_act,
                "pred_weight_gain_factor": pred_gain,
                "pred_weight_loss_factor": pred_loss,
                "gt_weight_gain_factor": 'nan',
                "gt_weight_loss_factor": 'nan'
            })

            conn_pred.close()
            conn_gt.close()
            # --- End collect ---

            meal_results.append({
                "user_id": user.id,
                "day": day + 1,
                "date": time.strftime("%Y-%m-%d"),
                "weight": round(new_weight, 2),
                "recommended_meal": "; ".join([f"{k}:{v:.2f}" for k, v in recommended_meal.food_items_quantity.items()]),
                "actual_meal": "; ".join([f"{k}:{v:.2f}" for k, v in actual_meal.food_items_quantity.items()]),
                "calories": round(actual_meal.calculate_nutritional_values()['calories'], 2)
            })

    # Write user info to CSV
    with open("user_info.csv", "w", newline='', encoding="utf-8") as csvfile:
        fieldnames = ["user_id", "height", "weight", "sex", "age", "estimated_days", "target_weight"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in user_info_results:
            writer.writerow(row)
    print("User information saved to user_info.csv")

    # Write meal results to CSV, sorted by user_id
    meal_results_sorted = sorted(meal_results, key=lambda x: x["user_id"])
    with open("user_meals.csv", "w", newline='', encoding="utf-8") as csvfile:
        fieldnames = ["user_id", "day", "date", "weight", "recommended_meal", "actual_meal", "calories"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in meal_results_sorted:
            writer.writerow(row)
    print("Meal simulation results saved to user_meals.csv")

    # Write comparison results to CSV
    with open("user_pred_gt_comparison.csv", "w", newline='', encoding="utf-8") as csvfile:
        fieldnames = [
            "day", "user_id", "date",
            "pred_food_preference", "gt_food_preference",
            "pred_activity_level", "gt_activity_level",
            "pred_weight_gain_factor", "pred_weight_loss_factor",
            "gt_weight_gain_factor", "gt_weight_loss_factor"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in comparison_results:
            writer.writerow(row)
    print("Prediction vs Ground Truth comparison saved to user_pred_gt_comparison.csv")