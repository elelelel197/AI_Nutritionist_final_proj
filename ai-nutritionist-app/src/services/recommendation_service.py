from typing import List, Dict, Tuple, Optional
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

class RecommendationService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize_tables()

    def _initialize_tables(self):
        """初始化必要的資料表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 創建推薦攝入量表（如果不存在）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recommended_intake (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sex TEXT NOT NULL,
                age_min INTEGER NOT NULL,
                age_max INTEGER NOT NULL,
                weight_min REAL NOT NULL,
                weight_max REAL NOT NULL,
                activity_level TEXT NOT NULL,
                goal TEXT NOT NULL,
                daily_calories REAL NOT NULL,
                protein_g REAL NOT NULL,
                carbohydrates_g REAL NOT NULL,
                fats_g REAL NOT NULL,
                fiber_g REAL NOT NULL
            )
        ''')
        
        # 插入默認推薦數據
        default_recommendations = [
            # 減重目標
            ('M', 20, 30, 60, 80, 'moderately active', 'weight_loss', 2200, 110, 250, 73, 30),
            ('F', 20, 30, 50, 65, 'moderately active', 'weight_loss', 1800, 90, 200, 60, 25),
            # 增肌目標
            ('M', 20, 30, 60, 80, 'moderately active', 'muscle_gain', 2800, 140, 350, 93, 35),
            ('F', 20, 30, 50, 65, 'moderately active', 'muscle_gain', 2300, 115, 290, 77, 30),
            # 維持目標
            ('M', 20, 30, 60, 80, 'moderately active', 'maintain', 2500, 125, 313, 83, 30),
            ('F', 20, 30, 50, 65, 'moderately active', 'maintain', 2000, 100, 250, 67, 25),
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO recommended_intake 
            (sex, age_min, age_max, weight_min, weight_max, activity_level, goal, 
             daily_calories, protein_g, carbohydrates_g, fats_g, fiber_g)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', default_recommendations)
        
        conn.commit()
        conn.close()

    def calculate_user_needs(self, user_data: Dict) -> Dict:
        """
        計算用戶的營養需求
        
        Args:
            user_data: 包含用戶資訊的字典
                {
                    'sex': 'M'/'F',
                    'age': 年齡,
                    'weight': 體重(kg),
                    'height': 身高(cm),
                    'activity_level': 'sedentary'/'lightly_active'/'moderately_active'/'very_active',
                    'goal': 'weight_loss'/'muscle_gain'/'maintain'
                }
        
        Returns:
            Dict: 包含計算後的營養需求
        """
        # 計算BMR（基礎代謝率）
        if user_data['sex'] == 'M':
            bmr = 10 * user_data['weight'] + 6.25 * user_data['height'] - 5 * user_data['age'] + 5
        else:
            bmr = 10 * user_data['weight'] + 6.25 * user_data['height'] - 5 * user_data['age'] - 161
        
        # 活動水平乘數
        activity_multipliers = {
            'sedentary': 1.2,
            'lightly_active': 1.375,
            'moderately_active': 1.55,
            'very_active': 1.725,
            'extremely_active': 1.9
        }
        
        activity_level = user_data.get('activity_level', 'moderately_active')
        tdee = bmr * activity_multipliers.get(activity_level, 1.55)
        
        # 根據目標調整熱量需求
        goal_adjustments = {
            'weight_loss': 0.85,  # 減少15%熱量
            'maintain': 1.0,      # 維持熱量
            'muscle_gain': 1.15   # 增加15%熱量
        }
        
        goal = user_data.get('goal', 'maintain')
        adjusted_calories = tdee * goal_adjustments.get(goal, 1.0)
        
        # 計算巨量營養素需求（基於熱量分配）
        # 蛋白質: 25%, 碳水: 50%, 脂肪: 25%
        protein_calories = adjusted_calories * 0.25
        carb_calories = adjusted_calories * 0.50
        fat_calories = adjusted_calories * 0.25
        
        # 轉換為克數（蛋白質和碳水: 4卡/克, 脂肪: 9卡/克）
        protein_g = protein_calories / 4
        carbs_g = carb_calories / 4
        fats_g = fat_calories / 9
        
        return {
            'daily_calories': round(adjusted_calories),
            'protein_g': round(protein_g, 1),
            'carbohydrates_g': round(carbs_g, 1),
            'fats_g': round(fats_g, 1),
            'fiber_g': 25,  # 默認纖維攝入量
            'tdee': round(tdee),
            'bmr': round(bmr)
        }

    def get_meal_recommendations(self, user_data: Dict, meal_type: str = "lunch", 
                               max_recommendations: int = 5) -> List[Dict]:
        """
        獲取個性化餐食推薦
        
        Args:
            user_data: 用戶數據
            meal_type: 餐食類型 (breakfast, lunch, dinner, snack)
            max_recommendations: 最大推薦數量
        
        Returns:
            List[Dict]: 推薦餐食列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 計算用戶營養需求
            user_needs = self.calculate_user_needs(user_data)
            
            # 獲取用戶今日已攝入營養
            today_intake = self._get_today_intake(conn, user_data.get('user_id', 1))
            
            # 計算剩餘營養需求
            remaining_needs = self._calculate_remaining_needs(user_needs, today_intake, meal_type)
            
            # 獲取食物數據
            food_data = pd.read_sql_query("SELECT * FROM food_nutrition", conn)
            
            # 根據餐食類型過濾食物
            meal_filters = {
                'breakfast': ['grain', 'fruit', 'dairy'],
                'lunch': ['protein', 'vegetable', 'grain'],
                'dinner': ['protein', 'vegetable', 'grain'],
                'snack': ['fruit', 'nuts', 'dairy']
            }
            
            filtered_foods = food_data[food_data['food_type'].isin(meal_filters.get(meal_type, []))]
            
            # 為食物評分
            scored_foods = []
            for _, food in filtered_foods.iterrows():
                score = self._score_food(food, remaining_needs, user_data)
                scored_foods.append((food, score))
            
            # 按分數排序並選擇最佳推薦
            scored_foods.sort(key=lambda x: x[1], reverse=True)
            recommendations = []
            
            for food, score in scored_foods[:max_recommendations]:
                food_dict = {
                    'food_id': food['food_id'],
                    'food_name': food['food_name'],
                    'food_type': food['food_type'],
                    'calories': food['calories'],
                    'protein': food['protein'],
                    'carbohydrates': food['carbohydrates'],
                    'fats': food['fats'],
                    'vitamins': food['vitamins'],
                    'minerals': food['minerals'],
                    'score': round(score, 2),
                    'recommended_quantity': self._calculate_recommended_quantity(food, remaining_needs)
                }
                recommendations.append(food_dict)
            
            conn.close()
            return recommendations
            
        except Exception as e:
            print(f"獲取餐食推薦時發生錯誤: {e}")
            return []

    def _get_today_intake(self, conn: sqlite3.Connection, user_id: int) -> Dict:
        """獲取用戶今日已攝入營養"""
        try:
            query = '''
                SELECT 
                    SUM(calories_consumed) as total_calories,
                    SUM(protein_consumed) as total_protein,
                    SUM(carbs_consumed) as total_carbs,
                    SUM(fats_consumed) as total_fats
                FROM user_history
                WHERE user_id = ? AND date = date('now')
            '''
            result = pd.read_sql_query(query, conn, params=(user_id,)).iloc[0]
            
            return {
                'calories': result['total_calories'] or 0,
                'protein': result['total_protein'] or 0,
                'carbs': result['total_carbs'] or 0,
                'fats': result['total_fats'] or 0
            }
        except:
            return {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0}

    def _calculate_remaining_needs(self, user_needs: Dict, today_intake: Dict, meal_type: str) -> Dict:
        """計算剩餘營養需求"""
        # 根據餐食類型分配每日需求的百分比
        meal_allocations = {
            'breakfast': 0.25,
            'lunch': 0.35,
            'dinner': 0.30,
            'snack': 0.10
        }
        
        allocation = meal_allocations.get(meal_type, 0.25)
        
        remaining = {
            'calories': max(0, user_needs['daily_calories'] * allocation - today_intake['calories']),
            'protein': max(0, user_needs['protein_g'] * allocation - today_intake['protein']),
            'carbs': max(0, user_needs['carbohydrates_g'] * allocation - today_intake['carbs']),
            'fats': max(0, user_needs['fats_g'] * allocation - today_intake['fats'])
        }
        
        return remaining

    def _score_food(self, food: pd.Series, remaining_needs: Dict, user_data: Dict) -> float:
        """為食物評分（基於論文中的4個指標）"""
        score = 0.0
        
        # 1. 營養均衡 (30%) - 檢查是否符合剩餘需求的比例
        nutrition_score = self._calculate_nutrition_balance(food, remaining_needs)
        score += nutrition_score * 0.3
        
        # 2. 幫助達成目標 (35%) - 基於用戶目標評分
        goal_score = self._calculate_goal_alignment(food, user_data)
        score += goal_score * 0.35
        
        # 3. 符合用戶偏好 (25%) - 這裡簡化處理，實際應該基於用戶歷史數據
        preference_score = self._calculate_preference_score(food, user_data)
        score += preference_score * 0.25
        
        # 4. 多樣性 (10%) - 需要用戶歷史數據，這裡簡化
        diversity_score = 0.7  # 默認分數
        score += diversity_score * 0.1
        
        return score

    def _calculate_nutrition_balance(self, food: pd.Series, remaining_needs: Dict) -> float:
        """計算營養平衡分數"""
        if remaining_needs['calories'] <= 0:
            return 0.0
        
        # 計算食物營養與剩餘需求的比例匹配度
        calorie_ratio = min(food['calories'] / remaining_needs['calories'], 1.0) if remaining_needs['calories'] > 0 else 0
        protein_ratio = min(food['protein'] / remaining_needs['protein'], 1.0) if remaining_needs['protein'] > 0 else 0
        carbs_ratio = min(food['carbohydrates'] / remaining_needs['carbs'], 1.0) if remaining_needs['carbs'] > 0 else 0
        fats_ratio = min(food['fats'] / remaining_needs['fats'], 1.0) if remaining_needs['fats'] > 0 else 0
        
        # 計算平均匹配度
        avg_ratio = (calorie_ratio + protein_ratio + carbs_ratio + fats_ratio) / 4
        
        return avg_ratio

    def _calculate_goal_alignment(self, food: pd.Series, user_data: Dict) -> float:
        """計算與用戶目標的對齊程度"""
        goal = user_data.get('goal', 'maintain')
        
        if goal == 'weight_loss':
            # 減重：偏好低熱量、高蛋白、高纖維食物
            score = (food['protein'] * 2 - food['calories'] * 0.1 - food['fats'] * 0.5) / 10
        elif goal == 'muscle_gain':
            # 增肌：偏好高蛋白、適中碳水食物
            score = (food['protein'] * 3 + food['carbohydrates'] * 0.5 - food['fats'] * 0.2) / 10
        else:  # maintain
            # 維持：均衡營養
            score = (food['protein'] + food['carbohydrates'] * 0.8 + food['fats'] * 0.5) / 10
        
        return max(0, min(1, score))

    def _calculate_preference_score(self, food: pd.Series, user_data: Dict) -> float:
        """計算偏好分數（簡化版本）"""
        # 這裡應該基於用戶歷史數據分析偏好
        # 目前使用食物類型的基本偏好
        type_preferences = {
            'fruit': 0.8,
            'vegetable': 0.7,
            'protein': 0.9,
            'grain': 0.8,
            'nuts': 0.6,
            'dairy': 0.7
        }
        
        return type_preferences.get(food['food_type'], 0.5)

    def _calculate_recommended_quantity(self, food: pd.Series, remaining_needs: Dict) -> int:
        """計算推薦食用量（克）"""
        if food['calories'] <= 0:
            return 100
        
        # 基於熱量需求計算推薦量
        base_quantity = (remaining_needs['calories'] / food['calories']) * 100
        recommended = min(max(50, base_quantity), 300)  # 限制在50-300克之間
        
        return round(recommended / 10) * 10  # 四捨五入到最近的10克

    def rate_meal(self, meal_data: Dict, user_needs: Dict) -> Dict:
        """
        評分單一餐食
        
        Args:
            meal_data: 餐食數據
            user_needs: 用戶營養需求
        
        Returns:
            Dict: 評分結果
        """
        try:
            total_score = 0
            feedback = []
            
            # 檢查熱量
            calorie_ratio = meal_data['calories'] / user_needs['daily_calories']
            if calorie_ratio <= 0.25:
                total_score += 25
                feedback.append("熱量控制良好")
            elif calorie_ratio <= 0.35:
                total_score += 20
                feedback.append("熱量適中")
            else:
                total_score += 10
                feedback.append("熱量稍高")
            
            # 檢查蛋白質
            protein_ratio = meal_data['protein'] / user_needs['protein_g']
            if protein_ratio >= 0.2:
                total_score += 25
                feedback.append("蛋白質充足")
            else:
                total_score += 10
                feedback.append("建議增加蛋白質")
            
            # 檢查營養平衡
            balance_score = self._calculate_meal_balance(meal_data)
            total_score += balance_score * 50
            
            # 總體評價
            if total_score >= 80:
                rating = "優秀"
            elif total_score >= 60:
                rating = "良好"
            elif total_score >= 40:
                rating = "一般"
            else:
                rating = "需改進"
            
            return {
                'total_score': total_score,
                'rating': rating,
                'feedback': feedback,
                'calorie_evaluation': self._evaluate_calorie_level(meal_data['calories'])
            }
            
        except Exception as e:
            print(f"評分餐食時發生錯誤: {e}")
            return {'total_score': 0, 'rating': '無法評分', 'feedback': [], 'calorie_evaluation': '未知'}

    def _calculate_meal_balance(self, meal_data: Dict) -> float:
        """計算餐食營養平衡分數"""
        total = meal_data['protein'] + meal_data['carbs'] + meal_data['fats']
        if total == 0:
            return 0.0
        
        # 理想比例：蛋白質25%, 碳水50%, 脂肪25%
        ideal_ratios = [0.25, 0.50, 0.25]
        actual_ratios = [
            meal_data['protein'] / total,
            meal_data['carbs'] / total,
            meal_data['fats'] / total
        ]
        
        # 計算與理想比例的差異
        balance_score = 1 - sum(abs(actual - ideal) for actual, ideal in zip(actual_ratios, ideal_ratios)) / 2
        return max(0, balance_score)

    def _evaluate_calorie_level(self, calories: float) -> str:
        """評估熱量水平"""
        if calories < 300:
            return "低熱量"
        elif calories < 600:
            return "中等熱量"
        elif calories < 900:
            return "高熱量"
        else:
            return "極高熱量"

    def generate_weekly_report(self, user_id: int) -> Dict:
        """生成每週營養報告"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 獲取最近7天的數據
            query = '''
                SELECT 
                    date,
                    SUM(calories_consumed) as daily_calories,
                    SUM(protein_consumed) as daily_protein,
                    SUM(carbs_consumed) as daily_carbs,
                    SUM(fats_consumed) as daily_fats
                FROM user_history
                WHERE user_id = ? AND date >= date('now', '-7 days')
                GROUP BY date
                ORDER BY date
            '''
            
            weekly_data = pd.read_sql_query(query, conn, params=(user_id,))
            
            # 計算平均值和趨勢
            avg_calories = weekly_data['daily_calories'].mean() if not weekly_data.empty else 0
            avg_protein = weekly_data['daily_protein'].mean() if not weekly_data.empty else 0
            
            conn.close()
            
            return {
                'period': '7天',
                'average_calories': round(avg_calories),
                'average_protein': round(avg_protein, 1),
                'data_points': len(weekly_data),
                'trend': 'stable'  # 簡化，實際應該計算趨勢
            }
            
        except Exception as e:
            print(f"生成週報時發生錯誤: {e}")
            return {}

    def close(self):
        """關閉資料庫連接"""
        pass  # 使用完畢後手動關閉連接
