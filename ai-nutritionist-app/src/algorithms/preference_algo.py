import sqlite3 as sql
import pandas as pd
from sklearn.linear_model import SGDClassifier
import numpy as np
from models.meal import Meal

# Load data from database
def fetch_meal_data():
    conn = sql.connect('user_history.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, food_name, quantity, meal_time FROM meals_log
    ''')
    actual_meals = cursor.fetchall()
    cursor.execute('''
        SELECT user_id, food_name, quantity, meal_time FROM recommended_meals_log
    ''')
    recommended_meals = cursor.fetchall()
    conn.close()
    return actual_meals, recommended_meals

# Prepare training data
def prepare_training_data(actual_meals, recommended_meals):
    # Combine and label data
    df_actual = pd.DataFrame(actual_meals, columns=['user_id', 'food_name', 'quantity', 'meal_time'])
    df_actual['was_recommended'] = 0
    df_actual['ate'] = 1

    df_recommended = pd.DataFrame(recommended_meals, columns=['user_id', 'food_name', 'quantity', 'meal_time'])
    df_recommended['was_recommended'] = 1
    # Mark as ate if present in actual meals
    df_recommended['ate'] = df_recommended.apply(
        lambda row: int(((df_actual['user_id'] == row['user_id']) & 
                         (df_actual['food_name'] == row['food_name']) & 
                         (df_actual['meal_time'] == row['meal_time'])).any()), axis=1)

    df = pd.concat([df_actual, df_recommended], ignore_index=True)
    # Encode food_name
    df['food_name_code'] = df['food_name'].astype('category').cat.codes
    X = df[['food_name_code', 'was_recommended', 'quantity']]
    y = df['ate']
    return X, y

# Train or update model
def train_or_update_model(model=None):
    actual_meals, recommended_meals = fetch_meal_data()
    X, y = prepare_training_data(actual_meals, recommended_meals)
    model = train_or_update_model(X, y)
    if model is None:
        model = SGDClassifier()
        model.partial_fit(X, y, classes=np.array([0, 1]))
    else:
        model.partial_fit(X, y)
    return model


# Predict user preference for a food
def predict_preference(model, user_id, food_name, was_recommended, quantity, food_name_list):
    food_code = pd.Series([food_name]).astype('category').cat.set_categories(food_name_list).cat.codes[0]
    X_new = np.array([[food_code, was_recommended, quantity]])
    preference_score = model.predict_proba(X_new)[0][1]  # Probability user will eat/like

    food_type = Meal.get_food_type_by_name(food_name)
    conn_user_pred = sql.connect('user_pred.db')
    cursor_user_pred = conn_user_pred.cursor()
    cursor_user_pred.execute('SELECT 1 FROM users_preference WHERE user_id = ?', (user_id,))
    exists = cursor_user_pred.fetchone()
    if exists:
        cursor_user_pred.execute('''
            UPDATE users_preference SET food_preference = ? WHERE user_id = ? AND food_name = ?
            ''', (preference_score, user_id, food_name)
            )
    else:
        cursor_user_pred.execute('''
            INSERT INTO users_preference (user_id, food_name, food_type, food_preference) 
            VALUES (?, ?, ?, ?)
            ''', (user_id, food_name, food_type, preference_score))
    conn_user_pred.commit()
    conn_user_pred.close()
    return preference_score


