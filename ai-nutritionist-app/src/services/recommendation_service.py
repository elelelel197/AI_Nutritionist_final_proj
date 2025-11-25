import sqlite3 as sql
from typing import List, Dict, Optional, Any
import math
from models.meal import Meal
import utils.nutrition_utils as nu_utils
from models.user import User
import numpy as np
from datetime import date,  timedelta

FOOD_NUTRTION_MATCH_SCORE_FACTOR = 0.5 # 食物營養匹配分數因子
FOOD_VARIETY_PENALTY_FACTOR = 0.1  # 每多吃一次同樣的食物，品種分數降低 0.1
LOOKBACK_DAYS = 5

NUTRITION_MATCH_SCORE_WEIGHT = 0.2
HEALTHY_SCORE_WEIGHT = 0.35
PREFERENCE_SCORE_WEIGHT = 0.3
NONREPEAT_SCORE_WEIGHT = 0.15

MEAL_FRUIT_RATIO = 0.15
MEAL_PROTEIN_RATIO = 0.15
MEAL_GRAINS_RATIO = 0.30
MEAL_VEGETABLE_RATIO = 0.25
MEAL_OIL_RATIO = 0.5
MEAL_DAIRY_RATIO = 0.10
MEAL_RATIO_TOLERANCE = 0.05
AVG_FOOD_RESELECT_COUNT = 5


class RecommendationService:
    """
    改良版 RecommendationService

    - 與 MealTracker 合作（傳入 MealTracker 實例以取得今日攝入）
    - food_nutrition 資料表應以 per_100g 為單位（見 MealTracker 實作）
    - recommended_intake 表會在空的情況下才插入預設建議
    """
    def __init__(self):
        pass


    # -----------------------
    # Core nutrition math
    # -----------------------
    @staticmethod
    def calculate_user_needs(user: User) -> Dict[str, float]:

        user_activity_level = user.get_user_activity_level()
        weight_gain_factor, weight_loss_factor = user.get_user_weight_gain_loss_factor()

        daily_cal = nu_utils.calculate_daily_caloric_needs(
            weight=user.weight,
            height=user.height,
            age=user.age,
            sex=user.sex,
            activity_level=user_activity_level
            )

        daily_cal = daily_cal * weight_gain_factor if user.target_weight > user.weight else daily_cal * weight_loss_factor
        if user.sex == 'M':
            daily_cal = max(daily_cal, 1500)  # Minimum
        else:
            daily_cal = max(daily_cal, 1200)  # Minimum
        
        # Macronutrient distribution ratios (can be adjusted based on goals)
        nutrient_ratios = nu_utils.calculate_macronutrient_distribution(daily_cal, user.weight,user.target_weight)

        return nutrient_ratios

    # -----------------------
    # Recommendation logic
    # -----------------------
    

    @staticmethod
    def get_meal_recommendations(user: User, time: date) -> Meal:
        meal_ratio = {
            'fruit': MEAL_FRUIT_RATIO,
            'protein': MEAL_PROTEIN_RATIO,
            'grains': MEAL_GRAINS_RATIO,
            'vegetable': MEAL_VEGETABLE_RATIO,
            'oil': MEAL_OIL_RATIO,
            'dairy': MEAL_DAIRY_RATIO
        }
        recommend_meal = Meal({}, time)
        conn_food_nutrition = sql.connect('food_nutrition.db')
        cursor_food_nutrition = conn_food_nutrition.cursor()
        user_needs = user.calculate_user_needs()

        for food_type in ['grains', 'protein', 'vegetable','fruit', 'oil', 'dairy']:
            cursor_food_nutrition.execute('''
                    SELECT food_name FROM food_nutrition
                    where food_type = ?
                    ''', (food_type,)
                    )
            result = cursor_food_nutrition.fetchall()
            food_list = [item[0] for item in result]
            food_chosen = food_list[0]
            total_score = 0.0
            reselect_count = 0
            # Food with higher score has higher chance to get selected
            while np.random.rand() > total_score :
                food_chosen = np.random.choice(food_list)
                healthy_score = RecommendationService.food_healthy_score(food_chosen, food_type)
                nutrition_match_score = RecommendationService.food_nutrition_match_score(food_chosen, recommend_meal, user_needs)
                nonrepeat_score = RecommendationService.food_nonrepeat_score(user, food_chosen)
                preference_score = RecommendationService.food_preference_score(user, food_chosen)
                total_score = nutrition_match_score * NUTRITION_MATCH_SCORE_WEIGHT + nonrepeat_score * NONREPEAT_SCORE_WEIGHT + preference_score * PREFERENCE_SCORE_WEIGHT + healthy_score * HEALTHY_SCORE_WEIGHT
                reselect_count += 1
            # The the more reselect_count the less ideal the food
            meal_ratio[food_type] += min((np.exp(AVG_FOOD_RESELECT_COUNT - reselect_count) - 1) * MEAL_RATIO_TOLERANCE, MEAL_RATIO_TOLERANCE)
            if food_nutrient := Meal.get_food_nutrition_by_name(food_chosen) and food_nutrient['calories'] > 0:
                recommend_meal.food_items_quantity[food_chosen] = user_needs['daily_calories'] * meal_ratio[food_type] / food_nutrient['calories'] * 100  # convert to grams
            else:
                recommend_meal.food_items_quantity[food_chosen] = 100.0  # default 100g if nutrition not found
            
        conn_food_nutrition.close()
        return recommend_meal






    # -----------------------
    # Scoring helpers
    # -----------------------
    @staticmethod
    def food_healthy_score(food, food_type) -> float:
        score = 1.0
        healthy_nutrition_composition = nu_utils.get_healthy_nutrition_composition(food_type)

        food_nutrition = nu_utils.get_food_nutrition_by_name(food)
        if not food_nutrition:
            return 0.5  # Default score if food nutrition not found

        # When the food's nutritional ratio is far from user's need, the score is lower
        score = sum(food_nutrition * healthy_nutrition_composition) / np.sqrt(sum(np.array(list(food_nutrition.values())) ** 2)) * sum((np.array(list(healthy_nutrition_composition.values())) ** 2))
        return score


    @staticmethod
    def food_nutrition_match_score(food, meal: Meal, user_needs: Dict[str, Any]) -> float:
        score = 1.0
        remaining = list(user_needs.items()) - meal.calculate_nutritional_values()
        food_nutrition = nu_utils.get_food_nutrition_by_name(food)
        if not food_nutrition:
            return 0.5  # Default score if food nutrition not found
        
        # When the food's nutritional ratio is far from user's need, the score is lower
        score = sum(food_nutrition * remaining) / np.sqrt(sum(np.array(list(food_nutrition.values())) ** 2)) * sum((np.array(list(remaining.values())) ** 2))
        return score


    

    # @staticmethod
    # def food_variety_score(meal: Meal, food_name: str) -> float:
    #     score = 1.0
    #     food_type_of_food = Meal.get_food_type_by_name(food_name)
    #     food_type_in_meal = meal.recommended_meal.get_food_type()
    #     for food_type in food_type_in_meal:
    #         if food_type_of_food == food_type:
    #             score *= FOOD_NUTRTION_MATCH_SCORE_FACTOR
    #     return score
            


    @staticmethod
    def food_preference_score(user: User, food_name: str) -> float:
        preference = user.get_user_food_preference(food_name)
        return preference


    # check if user consumed the same food in past meals
    @staticmethod
    def food_nonrepeat_score(user: User, food_name: str, time: date) -> float:
        lookback_time = timedelta(days=LOOKBACK_DAYS) 
        conn_user_gt = sql.connect('user_history.db')
        cursor_user_gt = conn_user_gt.cursor()
        cursor_user_gt.execute('''
            SELECT COUNT(*) FROM meals_log
            WHERE user_id = ? AND food_name = ? AND meal_time > ?
            ''', (user.id, food_name, time - lookback_time)
            )
        result = cursor_user_gt.fetchone()
        conn_user_gt.close()
        count = result[0] if result else 0
        # More consumption leads to lower variety score
        score = max(0.0, 1.0 - (count * FOOD_VARIETY_PENALTY_FACTOR)) 
        return score

    # @staticmethod
    # def _goal_alignment_score(food: Dict[str, Any], needs: Dict[str, float], provide: Dict[str, float], user_data: Dict[str, Any]) -> float:
    #     """
    #     根據用戶目標 (weight_loss/muscle_gain/maintain) 評估食物的對齊度。
    #     使用 protein-per-calorie 與 fiber/low-fat 特性來偏好減重或增肌。
    #     統一 normalize 到 0..1。
    #     """
    #     goal = user_data.get('goal', 'maintain')
    #     # avoid division by zero
    #     prov_cal = max(1e-6, provide.get('calories', 0.0))
    #     prot_per_100cal = (provide.get('protein', 0.0) / prov_cal) * 100.0  # g protein per 100 kcal

    #     # heuristics (可調)
    #     if goal == 'weight_loss':
    #         # prefer higher protein density and lower fat density
    #         prot_score = min(prot_per_100cal / 8.0, 1.0)  # ~8g/100kcal is very protein-dense
    #         fat_score = 1.0 - min((provide.get('fats', 0.0) / prov_cal) * 100.0 / 10.0, 1.0)
    #         return max(0.0, min(1.0, 0.7 * prot_score + 0.3 * fat_score))
    #     elif goal == 'muscle_gain':
    #         # prefer high protein and sufficient calories
    #         prot_score = min(prot_per_100cal / 10.0, 1.0)  # stricter
    #         cal_score = min(provide.get('calories', 0.0) / (needs['daily_calories'] * 0.2 + 1e-6), 1.0)
    #         return max(0.0, min(1.0, 0.6 * prot_score + 0.4 * cal_score))
    #     else:
    #         # maintain: prefer balanced
    #         # closeness to macro ratio (protein:carb:fat) as fraction of needs
    #         def ratio_score(key):
    #             need = {'protein': needs['protein_g'], 'carbs': needs['carbohydrates_g'], 'fats': needs['fats_g']}[key]
    #             if need <= 0:
    #                 return 1.0
    #             return min(provide.get(key, 0.0) / (need * 0.25 + 1e-6), 1.0)  # compare to meal allocation ~25%
    #         p = ratio_score('protein'); c = ratio_score('carbs'); f = ratio_score('fats')
    #         return (p + c + f) / 3.0


# -----------------------
# Example usage
# -----------------------
# if __name__ == "__main__":
#     # 範例假設：已有 MealTracker，並同一個 DB file
#     from meal_tracker import MealTracker  # 請確保 meal_tracker.py 可 import
#     mt = MealTracker("test_mealtracker.db")
#     rs = RecommendationService("test_mealtracker.db", meal_tracker=mt)

#     user = {
#         'user_id': 1,
#         'sex': 'F',
#         'age': 28,
#         'weight': 58,
#         'height': 162,
#         'activity_level': 'moderately_active',
#         'goal': 'muscle_gain'
#     }

#     recs = rs.get_meal_recommendations(user, meal_type='lunch', max_recommendations=5, preferences=['protein'])
#     import pprint; pprint.pprint(recs)