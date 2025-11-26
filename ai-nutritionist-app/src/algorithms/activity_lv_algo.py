import sqlite3 as sql
import pandas as pd
from sklearn.linear_model import SGDClassifier
import numpy as np
from models.user import User
from models.meal import Meal
import utils.file_paths as fp

class ActivityLvAlgo:
    @staticmethod
    def fetch_activity_data():
        # Fetch meal times for all users
        conn = sql.connect(fp.get_user_history_db_path())
        query = '''
            SELECT user_id, meal_time
            FROM meals_log
            GROUP BY user_id, meal_time
        '''
        df_meal_times = pd.read_sql_query(query, conn)
        conn.close()

        # Calculate calories for each meal using Meal.calculate_nutritional_values()
        meal_calories = []
        for _, row in df_meal_times.iterrows():
            meal = Meal.load_meal_from_db(row['user_id'], row['meal_time'])
            if meal:
                nutrition = meal.calculate_nutritional_values()
                calories = nutrition.get('calories', 0) if nutrition else 0
            else:
                calories = 0
            meal_calories.append({
                'user_id': row['user_id'],
                'meal_time': row['meal_time'],
                'consumed_calories': calories
            })
        df_meals = pd.DataFrame(meal_calories)
        df_meals['meal_time'] = pd.to_datetime(df_meals['meal_time'])

        # Fetch weight logs and calculate weight_diff per day
        conn = sql.connect(fp.get_user_history_db_path())
        df_weight = pd.read_sql_query('SELECT user_id, weight, log_time FROM weight_log', conn)
        conn.close()
        df_weight['log_time'] = pd.to_datetime(df_weight['log_time'])
        df_weight = df_weight.sort_values(['user_id', 'log_time'])
        weight_diff = df_weight.groupby('user_id')['weight'].diff().fillna(0)
        days_diff = df_weight.groupby('user_id')['log_time'].diff().dt.days.replace(0, 1).fillna(1)
        df_weight['weight_diff'] = weight_diff / days_diff

        # Merge meal and weight data
        df = pd.merge(df_meals, df_weight, left_on=['user_id', 'meal_time'], right_on=['user_id', 'log_time'], how='inner')

        # Fetch activity level labels
        conn = sql.connect(fp.get_user_pred_db_path())
        df_users = pd.read_sql_query('SELECT user_id, activity_level FROM users_activity_level', conn)
        conn.close()
        df = pd.merge(df, df_users, on='user_id', how='left')
        df['activity_level_code'] = df['activity_level'].astype('category').cat.codes

        # Prepare features and labels
        X = df[['consumed_calories', 'weight_diff']].replace([np.inf, -np.inf], np.nan).fillna(0)
        y = df['activity_level_code'].fillna(0)
        activity_categories = df['activity_level'].astype('category').cat.categories
        return X, y, activity_categories

    @staticmethod
    def fetch_average_calories(user_id, days=3):
        conn = sql.connect(fp.get_user_history_db_path())
        query = '''
            SELECT meal_time, food_name, quantity
            FROM meals_log
            WHERE user_id = ?
            ORDER BY meal_time DESC
        '''
        df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()
        if len(df) == 0:
            return None
        recent_meal_times = pd.to_datetime(df['meal_time'].unique()[:days])
        df['meal_time'] = pd.to_datetime(df['meal_time'])
        df = df[df['meal_time'].isin(recent_meal_times)]
        total_calories = 0
        for _, row in df.iterrows():
            meal = Meal({row['food_name']: row['quantity']}, row['meal_time'])
            nutrition = meal.calculate_nutritional_values()
            calories = nutrition.get('calories', 0) if nutrition else 0
            total_calories += calories
        avg_calories = total_calories / max(len(df), 1)
        return avg_calories

    @staticmethod
    def train_or_update_model(X, y, model=None):
        X = X.replace([np.inf, -np.inf], np.nan).fillna(0)
        y = y.loc[X.index].fillna(0)
        unique_classes = np.unique(y)
        if X.empty or y.empty or len(unique_classes) < 2:
            return model  # Not enough data or only one class
        if model is None:
            model = SGDClassifier()
            model.partial_fit(X, y, classes=unique_classes)
        else:
            model.partial_fit(X, y)
        return model

    @staticmethod
    def predict_activity_level(model, user: User, activity_categories, lookback_days=3):
        if model is None or len(activity_categories) == 0:
            return None
        avg_calories = ActivityLvAlgo.fetch_average_calories(user.id, lookback_days)
        if avg_calories is None:
            avg_calories = user.calculate_user_needs()['calories']
        conn = sql.connect(fp.get_user_history_db_path())
        df_weight = pd.read_sql_query('''
            SELECT weight, log_time FROM weight_log
            WHERE user_id = ? 
            ORDER BY log_time DESC
            LIMIT 2
            ''', conn, params=(user.id,))
        conn.close()
        weight_diff = 0
        if len(df_weight) > 1:
            df_weight['log_time'] = pd.to_datetime(df_weight['log_time'])
            days = (df_weight['log_time'].iloc[0] - df_weight['log_time'].iloc[1]).days
            if days == 0:
                days = 1
            weight_diff = (df_weight['weight'].iloc[0] - df_weight['weight'].iloc[1]) / days
        X_new = np.array([[avg_calories, weight_diff]])
        pred_code = model.predict(X_new)[0]
        conn = sql.connect(fp.get_user_pred_db_path())
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users_activity_level WHERE user_id = ?', (user.id,))
        exists = cursor.fetchone()
        if exists:
            cursor.execute('UPDATE users_activity_level SET activity_level = ? WHERE user_id = ?', (activity_categories[pred_code], user.id))
        else:
            cursor.execute('INSERT INTO users_activity_level (user_id, activity_level) VALUES (?, ?)', (user.id, activity_categories[pred_code]))
        conn.commit()
        conn.close()
        return activity_categories[pred_code]