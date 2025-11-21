from typing import List, Dict, Any
import sqlite3

class RecommendationService:
    def __init__(self, db_path: str):
        # use Row factory so we can access columns by name and avoid index errors
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    # 主功能：根據使用者的性別與年齡取得推薦餐點
    def get_meal_recommendations(self, user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        self.cursor.execute(
            "SELECT * FROM recommended_intake WHERE sex = ? AND age = ?",
            (user_data.get('sex'), user_data.get('age'))
        )
        rec_row = self.cursor.fetchone()
        if not rec_row:
            return []

        recommended_intake = dict(rec_row)

        self.cursor.execute("SELECT * FROM food_nutrition")
        food_rows = self.cursor.fetchall()

        recommendations: List[Dict[str, Any]] = []
        for row in food_rows:
            food = dict(row)
            if self.is_meal_healthy(food, recommended_intake):
                # try common column names, fall back to raw dict if not present
                name = food.get('name') or food.get('food_name') or food.get('food') or food.get('title') or ''
                calories = food.get('calories') or food.get('cal') or food.get('energy')
                protein = food.get('protein') or food.get('pro')
                carbs = food.get('carbs') or food.get('carbohydrates')
                fat = food.get('fat') or food.get('fats')

                # collect remaining micronutrients
                ignored_keys = {'id','name','food_name','food','title','calories','cal','energy','protein','pro','carbs','carbohydrates','fat','fats'}
                micronutrients = {k: v for k, v in food.items() if k not in ignored_keys}

                recommendations.append({
                    'food_name': name,
                    'calories': calories,
                    'protein': protein,
                    'carbs': carbs,
                    'fat': fat,
                    'micronutrients': micronutrients
                })

        return recommendations

    # 判斷餐點是否健康
    def is_meal_healthy(self, food: Dict[str, Any], recommended_intake: Dict[str, Any]) -> bool:
        def to_float(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return None


        food_cal = to_float(food.get('calories') or food.get('cal') or food.get('energy'))
        food_pro = to_float(food.get('protein') or food.get('pro'))
        food_carb = to_float(food.get('carbs') or food.get('carbohydrates'))
        food_fat = to_float(food.get('fat') or food.get('fats'))

        rec_cal = to_float(recommended_intake.get('calories') or recommended_intake.get('cal') or recommended_intake.get('recommended_calories'))
        rec_pro = to_float(recommended_intake.get('protein') or recommended_intake.get('pro') or recommended_intake.get('recommended_protein'))
        rec_carb = to_float(recommended_intake.get('carbs') or recommended_intake.get('carbohydrates') or recommended_intake.get('recommended_carbs'))
        rec_fat = to_float(recommended_intake.get('fat') or recommended_intake.get('fats') or recommended_intake.get('recommended_fat'))

        if None in (food_cal, food_pro, food_carb, food_fat, rec_cal, rec_pro, rec_carb, rec_fat):
            return False

        # 基本健康規則
        return (
            food_cal <= rec_cal and
            food_pro >= rec_pro and
            food_carb <= rec_carb and
            food_fat <= rec_fat
        )

     # 評分
    def rate_meal(self, meal_data: Dict[str, Any]) -> str:
        try:
            calories = float(meal_data.get('calories') or meal_data.get('cal') or meal_data.get('energy'))
        except (TypeError, ValueError, KeyError):
            return "please enter again"

        if calories < 500:
            return "Healthy"
        elif calories < 1000:
            return "Moderate"
        else:
            return "Unhealthy"

    def close(self):
        self.connection.close()
