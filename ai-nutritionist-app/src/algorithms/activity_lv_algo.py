import sqlite3 as sql
import pandas as pd
from sklearn.linear_model import SGDClassifier
import numpy as np
from models.user import User
from models.meal import Meal

# Load data from database
def fetch_activity_data():
    conn = sql.connect('user_history.db')
    # Get total consumed calories per user per day from meals_log
    query = '''
        SELECT user_id, meal_time, SUM(quantity * f.calories / 100) AS consumed_calories
        FROM meals_log m
        JOIN food_nutrition f ON m.food_name = f.food_name
        GROUP BY user_id, meal_time
    '''
    df_meals = pd.read_sql_query(query, conn)

    # Get weight log per user per day
    df_weight = pd.read_sql_query('SELECT user_id, weight, log_time FROM weight_log', conn)
    df_weight = df_weight.sort_values(['user_id', 'log_time'])
    df_weight['weight_diff'] = df_weight.groupby('user_id')['weight'].diff().fillna(0) / df_weight.groupby('user_id')['log_time'].diff().dt.days.fillna(1)

    # Merge on user_id and date
    df = pd.merge(df_meals, df_weight, left_on=['user_id', 'meal_time'], right_on=['user_id', 'log_time'], how='inner')

    # You need to provide activity_level labels for supervised training
    # For demo, let's assume you have a column 'activity_level' in users table
    df_users = pd.read_sql_query('SELECT user_id, activity_level FROM users', conn)
    df = pd.merge(df, df_users, on='user_id', how='left')

    conn.close()
    # Encode activity_level
    df['activity_level_code'] = df['activity_level'].astype('category').cat.codes
    X = df[['consumed_calories', 'weight_diff']]
    y = df['activity_level_code']
    activity_categories = df['activity_level'].astype('category').cat.categories
    return X, y, activity_categories

def fetch_average_calories(user_id, days=3):
    conn = sql.connect('user_history.db')
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
    # drop meals older than last three recorded meal_time entries
    recent_meal_times = df['meal_time'].unique()[:days]
    df = df[df['meal_time'].isin(recent_meal_times)]

    total_calories = 0
    for _, row in df.iterrows():
        meal = Meal({row['food_name']: row['quantity']}, row['meal_time'])
        calories = meal.calculate_nutritional_values()['calories']
        total_calories += calories

    avg_calories = total_calories / len(df)
    return avg_calories

# Train or update model
def train_or_update_model(X, y, model=None):
    if model is None:
        model = SGDClassifier()
        model.partial_fit(X, y, classes=np.unique(y))
    else:
        model.partial_fit(X, y)
    return model

# Predict activity level
def predict_activity_level(model, user: User, activity_categories, lookback_days=3):
    # Try to fetch average calories from past few days
    avg_calories = fetch_average_calories(user.id, lookback_days)
    if avg_calories is None:
        # If not enough data, use calculated user needs
        avg_calories = user.calculate_user_needs()['calories']
    # get users last recorded weights
    conn = sql.connect('user_history.db')
    df_weight = pd.read_sql_query('''
        SELECT weight, log_time FROM weight_log
        WHERE user_id = ? 
        ORDER BY log_time DESC
        LIMIT 2
        ''', conn, params=(user.id,)
        )
    conn.close()
    weight_diff = df_weight['weight'].iloc[0] - df_weight['weight'].iloc[1] / df_weight['log_time'].diff().dt.days.fillna(1).iloc[1] if len(df_weight) > 1 else 0
    X_new = np.array([avg_calories, weight_diff])
    pred_code = model.predict(X_new)[0]
    # update user activity level in database
    conn = sql.connect('user_pred.db')
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

# Example usage
# if __name__ == "__main__":
#     X, y, activity_categories = fetch_activity_data()
#     model = train_or_update_model(X, y)
#     # Example input: consumed_calories and weight_diff
#     example_input = [2200, -0.5]
#     predicted_level = predict_activity_level(model, *example_input, activity_categories)
#     print(f"Predicted activity level: {predicted_level}")