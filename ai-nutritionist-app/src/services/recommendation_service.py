from typing import List, Dict
import sqlite3

class RecommendationService:
    def __init__(self, db_path: str):
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

    def get_meal_recommendations(self, user_data: Dict) -> List[Dict]:
        # Fetch recommended intake based on user data
        self.cursor.execute("SELECT * FROM recommended_intake WHERE sex = ? AND age = ?", 
                            (user_data['sex'], user_data['age']))
        recommended_intake = self.cursor.fetchone()

        # Fetch food nutrition data
        self.cursor.execute("SELECT * FROM food_nutrition")
        food_nutrition_data = self.cursor.fetchall()

        # Generate recommendations based on decision tree logic
        recommendations = []
        for food in food_nutrition_data:
            if self.is_meal_healthy(food, recommended_intake):
                recommendations.append({
                    'food_name': food[0],
                    'calories': food[1],
                    'macronutrients': food[2:5],  # Assuming macronutrients are in columns 2-4
                    'micronutrients': food[5:]     # Assuming micronutrients are in remaining columns
                })

        return recommendations

    def is_meal_healthy(self, food: tuple, recommended_intake: tuple) -> bool:
        # Implement decision tree logic to evaluate if the meal is healthy
        # This is a placeholder for actual decision tree logic
        return food[1] <= recommended_intake[1]  # Example: check if calories are within recommended intake

    def rate_meal(self, meal_data: Dict) -> str:
        # Placeholder for meal rating logic
        if meal_data['calories'] < 500:
            return "Healthy"
        elif meal_data['calories'] < 1000:
            return "Moderate"
        else:
            return "Unhealthy"

    def close(self):
        self.connection.close()