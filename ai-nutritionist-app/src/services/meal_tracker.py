from datetime import datetime
import sqlite3
import json
from typing import List, Dict, Any, Optional

class MealTracker:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


    # 記錄餐點
    def log_meal(self, user_id: int, meal_details: Any) -> None:
        try:
            # ensure meal_details is storable
            meal_json = meal_details if isinstance(meal_details, str) else json.dumps(meal_details)
            date_str = datetime.now().isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_history (user_id, meal_details, date)
                    VALUES (?, ?, ?)
                ''', (user_id, meal_json, date_str))
                # with 會自動 commit
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to log meal for user {user_id}: {e}")

    # 取得該使用者所有飲食紀錄
    def get_meal_history(self, user_id: int) -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT meal_details, date
                    FROM user_history
                    WHERE user_id = ?
                    ORDER BY date DESC
                ''', (user_id,))
                rows = cursor.fetchall()
                history: List[Dict[str, Any]] = []
                for r in rows:
                    meal_raw = r['meal_details']
                    try:
                        meal = json.loads(meal_raw)
                    except Exception:
                        meal = meal_raw
                    history.append({'meal_details': meal, 'date': r['date']})
                return history
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to fetch meal history for user {user_id}: {e}")

    # 取得最新體重
    def get_current_weight(self, user_id: int) -> Optional[float]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT weight FROM user_history
                    WHERE user_id = ?
                    AND weight IS NOT NULL
                    ORDER BY date DESC
                    LIMIT 1
                ''', (user_id,))
                weight_row = cursor.fetchone()
                if not weight_row:
                    return None
                weight = weight_row['weight']
                try:
                    return float(weight)
                except (TypeError, ValueError):
                    return None
        except sqlite3.Error as e:
        
            raise RuntimeError(f"Failed to fetch current weight for user {user_id}: {e}")

    # 更新體重
    def update_weight(self, user_id: int, new_weight: float) -> None:
        try:
            date_str = datetime.now().isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_history (user_id, weight, date)
                    VALUES (?, ?, ?)
                ''', (user_id, new_weight, date_str))
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to update weight for user {user_id}: {e}")
