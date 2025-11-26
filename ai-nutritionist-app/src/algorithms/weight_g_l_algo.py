import sqlite3 as sql
from datetime import date, datetime, timedelta
from models.user import User
from utils.nutrition_utils import NutritionUtils
import utils.file_paths as fp

class WeightGLAlgo:
    @staticmethod
    def get_ideal_weight_gain_loss_factor(user: User):
        conn_user_history = sql.connect(fp.get_user_history_db_path())
        cursor = conn_user_history.cursor()
        cursor.execute('''
            SELECT weight, log_time FROM weight_log
            WHERE user_id = ?
            ORDER BY log_time ASC
        ''', (user.id,))
        weight_data = [(item[0], datetime.strptime(item[1], '%Y-%m-%d')) for item in cursor.fetchall()]
        conn_user_history.close()

        if not weight_data:
            print("No weight data available for user.")
            return 1.1, 0.9

        last_log_time = weight_data[-1][1]
        final_time = weight_data[0][1] + timedelta(days=user.estimated_days)
        if last_log_time > final_time:
            print("Time exceeds final time.")
            return 1.1, 0.9
        remaining_days = (final_time - last_log_time).days
        daily_weight_change = (user.target_weight - user.weight) / remaining_days
        daily_calories_needs = NutritionUtils.calculate_daily_caloric_needs(user.weight, user.height, user.age, user.sex, user.get_user_activity_level())
        if user.weight > user.target_weight:
            ideal_weight_loss_factor = (daily_calories_needs + daily_weight_change * 7700) / daily_calories_needs
            ideal_weight_gain_factor = 1 / ideal_weight_loss_factor
        else:
            ideal_weight_gain_factor = (daily_calories_needs + daily_weight_change * 7700) / daily_calories_needs
            ideal_weight_loss_factor = 1 / ideal_weight_gain_factor
        return ideal_weight_gain_factor, ideal_weight_loss_factor

    @staticmethod
    def update_weight_gain_loss_factor(user: User):
        factors = WeightGLAlgo.get_ideal_weight_gain_loss_factor(user)
        conn = sql.connect(fp.get_user_pred_db_path())
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM user_weight_gain_loss_factor WHERE user_id = ?', (user.id,))
        exists = cursor.fetchone()
        if exists:
            cursor.execute('UPDATE user_weight_gain_loss_factor SET weight_gain_factor = ?, weight_loss_factor = ? WHERE user_id = ?', (factors[0], factors[1], user.id))
        else:
            cursor.execute('INSERT INTO user_weight_gain_loss_factor (user_id, weight_gain_factor, weight_loss_factor) VALUES (?, ?, ?)', (user.id, factors[0], factors[1]))
        conn.commit()
        conn.close()
        return factors