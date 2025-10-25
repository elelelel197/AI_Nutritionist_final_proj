from sklearn.tree import DecisionTreeClassifier
import pandas as pd
import sqlite3

class DecisionTreeNutritionist:
    def __init__(self, db_path):
        self.db_path = db_path
        self.model = DecisionTreeClassifier()
        self.food_data = self.load_food_data()
        self.recommended_intake = self.load_recommended_intake()

    def load_food_data(self):
        conn = sqlite3.connect(self.db_path)
        query = "SELECT * FROM food_nutrition"
        food_data = pd.read_sql_query(query, conn)
        conn.close()
        return food_data

    def load_recommended_intake(self):
        conn = sqlite3.connect(self.db_path)
        query = "SELECT * FROM recommended_intake"
        recommended_intake = pd.read_sql_query(query, conn)
        conn.close()
        return recommended_intake

    def train_model(self):
        features = self.food_data[['calories', 'protein', 'carbs', 'fat']]
        labels = self.food_data['rating']
        self.model.fit(features, labels)

    def rate_meal(self, meal_nutrition):
        meal_features = [[meal_nutrition['calories'], meal_nutrition['protein'], meal_nutrition['carbs'], meal_nutrition['fat']]]
        rating = self.model.predict(meal_features)
        return rating[0]

    def recommend_meal(self, user_data):
        # Logic to recommend meals based on user data and decision tree
        # This is a placeholder for the actual recommendation logic
        recommended_meals = self.food_data[self.food_data['calories'] <= user_data['caloric_needs']]
        return recommended_meals[['food_name', 'calories', 'protein', 'carbs', 'fat']]