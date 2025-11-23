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
        # 使用營養值當作特徵
        features = self.food_data[['calories', 'protein', 'carbs', 'fat']]

        # rating 當標籤（務必確保存在）
        if 'rating' not in self.food_data.columns:
            raise ValueError("food_nutrition 資料表缺少 rating 欄位。")

        labels = self.food_data['rating']

        # 訓練模型
        self.model.fit(features, labels)

 
    def rate_meal(self, meal_nutrition):
        meal_features = [[
            meal_nutrition['calories'],
            meal_nutrition['protein'],
            meal_nutrition['carbs'],
            meal_nutrition['fat']
        ]]
        rating = self.model.predict(meal_features)
        return int(rating[0])

    def get_user_recommended_intake(self, sex, age):
        df = self.recommended_intake
        result = df[(df['sex'] == sex) & (df['age'] == age)]

        if result.empty:
            return None  # 找不到建議值

        return result.iloc[0]  # 回傳 series

  
    def recommend_meal(self, user_data, top_k=5):
        """
        user_data:
            {
                'sex': 'M' or 'F',
                'age': 20,
                'goal': 'lose_weight' or 'gain_muscle' or 'healthy'
            }
        """

        # 先獲取該使用者建議攝取值
        rec_intake = self.get_user_recommended_intake(
            user_data['sex'],
            user_data['age']
        )

        if rec_intake is None:
            raise ValueError("查無該年齡與性別的 recommended intake 資料。")

        # 用模型預測每個食物的 rating
        X = self.food_data[['calories', 'protein', 'carbs', 'fat']]
        self.food_data['predicted_rating'] = self.model.predict(X)

        # 根據使用者目標做不同權重篩選
        df = self.food_data.copy()

        goal = user_data.get("goal", "healthy")

        # 🌟 減脂：低卡、高蛋白優先
        if goal == "lose_weight":
            df = df[df['calories'] <= rec_intake['calories']]
            df = df.sort_values(
                by=['predicted_rating', 'protein', 'calories'],
                ascending=[False, False, True]
            )

        # 🌟 增肌：高蛋白優先
        elif goal == "gain_muscle":
            df = df.sort_values(
                by=['protein', 'predicted_rating'],
                ascending=[False, False]
            )

        # 🌟 一般健康飲食
        else:
            df = df.sort_values(
                by=['predicted_rating'],
                ascending=False
            )

        # 取前 top_k
        return df[['food_name', 'calories', 'protein', 'carbs', 'fat', 'predicted_rating']].head(top_k)
