from datetime import datetime, date
import sqlite3
from typing import List, Dict, Optional

class MealTracker:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        """創建必要的資料表（如果不存在）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 創建用戶歷史記錄表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                current_weight FLOAT,
                meal_consumed TEXT,
                calories_consumed FLOAT,
                protein_consumed FLOAT,
                carbs_consumed FLOAT,
                fats_consumed FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def log_meal(self, user_id: int, food_id: int, quantity: float = 100) -> bool:
        """
        記錄用戶的一餐
        
        Args:
            user_id: 用戶ID
            food_id: 食物ID
            quantity: 食物重量（克），預設100克
            
        Returns:
            bool: 是否成功記錄
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 獲取食物營養資訊
            cursor.execute('''
                SELECT calories, protein, carbohydrates, fats 
                FROM food_nutrition 
                WHERE food_id = ?
            ''', (food_id,))
            food_data = cursor.fetchone()
            
            if not food_data:
                raise ValueError(f"食物ID {food_id} 不存在")
            
            calories, protein, carbs, fats = food_data
            
            # 計算實際攝入量（基於數量）
            actual_calories = (calories * quantity) / 100
            actual_protein = (protein * quantity) / 100
            actual_carbs = (carbs * quantity) / 100
            actual_fats = (fats * quantity) / 100
            
            # 獲取食物名稱
            cursor.execute('SELECT food_name FROM food_nutrition WHERE food_id = ?', (food_id,))
            food_name = cursor.fetchone()[0]
            
            # 記錄到資料庫
            cursor.execute('''
                INSERT INTO user_history 
                (user_id, date, meal_consumed, calories_consumed, protein_consumed, carbs_consumed, fats_consumed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, date.today(), food_name, actual_calories, actual_protein, actual_carbs, actual_fats))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"記錄餐食時發生錯誤: {e}")
            return False

    def log_meal_with_details(self, user_id: int, meal_details: Dict) -> bool:
        """
        使用詳細資訊記錄餐食
        
        Args:
            user_id: 用戶ID
            meal_details: 包含餐食詳細資訊的字典
                {
                    'foods': [{'food_id': 1, 'quantity': 150}, ...],
                    'custom_food': '自定義食物名稱',  # 可選
                    'custom_calories': 200,  # 可選
                    'notes': '餐食備註'  # 可選
                }
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            total_calories = 0
            total_protein = 0
            total_carbs = 0
            total_fats = 0
            food_names = []
            
            # 處理預定義食物
            for food_item in meal_details.get('foods', []):
                cursor.execute('''
                    SELECT food_name, calories, protein, carbohydrates, fats 
                    FROM food_nutrition 
                    WHERE food_id = ?
                ''', (food_item['food_id'],))
                food_data = cursor.fetchone()
                
                if food_data:
                    food_name, calories, protein, carbs, fats = food_data
                    quantity = food_item.get('quantity', 100)
                    
                    # 計算實際營養值
                    actual_calories = (calories * quantity) / 100
                    actual_protein = (protein * quantity) / 100
                    actual_carbs = (carbs * quantity) / 100
                    actual_fats = (fats * quantity) / 100
                    
                    total_calories += actual_calories
                    total_protein += actual_protein
                    total_carbs += actual_carbs
                    total_fats += actual_fats
                    food_names.append(f"{food_name}({quantity}g)")
            
            # 處理自定義食物
            if 'custom_food' in meal_details:
                food_names.append(meal_details['custom_food'])
                total_calories += meal_details.get('custom_calories', 0)
                # 自定義食物的其他營養素可以根據需要添加
            
            meal_description = ", ".join(food_names)
            if 'notes' in meal_details:
                meal_description += f" - {meal_details['notes']}"
            
            # 記錄到資料庫
            cursor.execute('''
                INSERT INTO user_history 
                (user_id, date, meal_consumed, calories_consumed, protein_consumed, carbs_consumed, fats_consumed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, date.today(), meal_description, total_calories, total_protein, total_carbs, total_fats))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"記錄詳細餐食時發生錯誤: {e}")
            return False

    def get_meal_history(self, user_id: int, days: int = 7) -> List[Dict]:
        """
        獲取用戶的飲食歷史
        
        Args:
            user_id: 用戶ID
            days: 要查詢的天數，預設7天
            
        Returns:
            List[Dict]: 飲食記錄列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT date, meal_consumed, calories_consumed, protein_consumed, carbs_consumed, fats_consumed
                FROM user_history
                WHERE user_id = ? AND date >= date('now', ?)
                ORDER BY date DESC, id DESC
            ''', (user_id, f'-{days} days'))
            
            meals = []
            for row in cursor.fetchall():
                meals.append({
                    'date': row[0],
                    'meal_consumed': row[1],
                    'calories_consumed': row[2] or 0,
                    'protein_consumed': row[3] or 0,
                    'carbs_consumed': row[4] or 0,
                    'fats_consumed': row[5] or 0
                })
            
            conn.close()
            return meals
            
        except Exception as e:
            print(f"獲取飲食歷史時發生錯誤: {e}")
            return []

    def get_daily_summary(self, user_id: int, target_date: str = None) -> Dict:
        """
        獲取指定日期的營養攝入摘要
        
        Args:
            user_id: 用戶ID
            target_date: 目標日期（YYYY-MM-DD），預設為今天
            
        Returns:
            Dict: 營養摘要
        """
        if target_date is None:
            target_date = date.today().isoformat()
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    SUM(calories_consumed) as total_calories,
                    SUM(protein_consumed) as total_protein,
                    SUM(carbs_consumed) as total_carbs,
                    SUM(fats_consumed) as total_fats
                FROM user_history
                WHERE user_id = ? AND date = ?
            ''', (user_id, target_date))
            
            result = cursor.fetchone()
            conn.close()
            
            return {
                'date': target_date,
                'total_calories': result[0] or 0,
                'total_protein': result[1] or 0,
                'total_carbs': result[2] or 0,
                'total_fats': result[3] or 0
            }
            
        except Exception as e:
            print(f"獲取每日摘要時發生錯誤: {e}")
            return {
                'date': target_date,
                'total_calories': 0,
                'total_protein': 0,
                'total_carbs': 0,
                'total_fats': 0
            }

    def get_current_weight(self, user_id: int) -> Optional[float]:
        """
        獲取用戶當前體重
        
        Args:
            user_id: 用戶ID
            
        Returns:
            Optional[float]: 當前體重，如果不存在則返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT current_weight FROM user_history
                WHERE user_id = ? AND current_weight IS NOT NULL
                ORDER BY date DESC, id DESC
                LIMIT 1
            ''', (user_id,))
            
            weight = cursor.fetchone()
            conn.close()
            return weight[0] if weight else None
            
        except Exception as e:
            print(f"獲取當前體重時發生錯誤: {e}")
            return None

    def update_weight(self, user_id: int, new_weight: float) -> bool:
        """
        更新用戶體重
        
        Args:
            user_id: 用戶ID
            new_weight: 新體重（公斤）
            
        Returns:
            bool: 是否成功更新
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_history (user_id, date, current_weight)
                VALUES (?, ?, ?)
            ''', (user_id, date.today(), new_weight))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"更新體重時發生錯誤: {e}")
            return False

    def get_weight_history(self, user_id: int, days: int = 30) -> List[Dict]:
        """
        獲取用戶體重歷史
        
        Args:
            user_id: 用戶ID
            days: 要查詢的天數
            
        Returns:
            List[Dict]: 體重記錄列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT date, current_weight
                FROM user_history
                WHERE user_id = ? AND current_weight IS NOT NULL AND date >= date('now', ?)
                ORDER BY date ASC
            ''', (user_id, f'-{days} days'))
            
            weight_history = []
            for row in cursor.fetchall():
                weight_history.append({
                    'date': row[0],
                    'weight': row[1]
                })
            
            conn.close()
            return weight_history
            
        except Exception as e:
            print(f"獲取體重歷史時發生錯誤: {e}")
            return []
