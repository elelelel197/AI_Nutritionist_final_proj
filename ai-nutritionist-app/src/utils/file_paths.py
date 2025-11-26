import os

# The abs path to the src directory
def get_user_history_db_path():
    return os.path.join(os.path.dirname(__file__), '..', 'database', 'user_history.db')

def get_user_pred_db_path():
    return os.path.join(os.path.dirname(__file__), '..', 'database', 'user_pred.db')

def get_user_gt_db_path():
    return os.path.join(os.path.dirname(__file__), '..', 'database', 'user_gt.db')

def get_food_nutrition_db_path():
    return os.path.join(os.path.dirname(__file__), '..', 'database', 'food_nutrition.db')