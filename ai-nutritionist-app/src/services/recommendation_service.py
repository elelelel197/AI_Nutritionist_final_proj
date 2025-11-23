import sqlite3
from typing import List, Dict, Optional, Any
import math

# 假設 MealTracker 位於 meal_tracker.py 中並已實作 get_today_intake()
from meal_tracker import MealTracker

class RecommendationService:
    """
    改良版 RecommendationService

    - 與 MealTracker 合作（傳入 MealTracker 實例以取得今日攝入）
    - food_nutrition 資料表應以 per_100g 為單位（見 MealTracker 實作）
    - recommended_intake 表會在空的情況下才插入預設建議
    """
    def __init__(self, db_path: str, meal_tracker: Optional[Any] = None):
        """
        db_path: sqlite DB path（與 MealTracker 共用同一 DB 最佳）
        meal_tracker: 可選的 MealTracker 實例（若傳入，會用它來取得今日攝入）
        """
        self.db_path = db_path
        self.meal_tracker = meal_tracker
        self._initialize_tables()

    # -----------------------
    # DB helpers
    # -----------------------
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_tables(self) -> None:
        """建立 recommended_intake 表（若不存在），且只在表為空時插入預設資料。"""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('''
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
                    fiber_g REAL NOT NULL,
                    UNIQUE(sex, age_min, age_max, weight_min, weight_max, activity_level, goal)
                )
            ''')
            # 只在表為空時插入預設值，避免重複
            cur.execute('SELECT COUNT(1) as cnt FROM recommended_intake')
            cnt = cur.fetchone()['cnt']
            if cnt == 0:
                default_recommendations = [
                    # sample defaults (可依需求擴充)
                    ('M', 20, 30, 60, 80, 'moderately_active', 'weight_loss', 2200, 110, 250, 73, 30),
                    ('F', 20, 30, 50, 65, 'moderately_active', 'weight_loss', 1800, 90, 200, 60, 25),
                    ('M', 20, 30, 60, 80, 'moderately_active', 'muscle_gain', 2800, 140, 350, 93, 35),
                    ('F', 20, 30, 50, 65, 'moderately_active', 'muscle_gain', 2300, 115, 290, 77, 30),
                    ('M', 20, 30, 60, 80, 'moderately_active', 'maintain', 2500, 125, 313, 83, 30),
                    ('F', 20, 30, 50, 65, 'moderately_active', 'maintain', 2000, 100, 250, 67, 25),
                ]
                cur.executemany('''
                    INSERT OR IGNORE INTO recommended_intake
                    (sex, age_min, age_max, weight_min, weight_max, activity_level, goal, daily_calories, protein_g, carbohydrates_g, fats_g, fiber_g)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', default_recommendations)
            conn.commit()

    # -----------------------
    # Core nutrition math
    # -----------------------
    def calculate_user_needs(self, user_data: Dict[str, Any]) -> Dict[str, float]:
        """
        計算用戶需求（BMR + TDEE + 目標調整）
        user_data: {sex, age, weight(kg), height(cm), activity_level, goal}
        返回: {daily_calories, protein_g, carbohydrates_g, fats_g, fiber_g, tdee, bmr}
        """
        sex = user_data.get('sex', 'M')
        age = user_data.get('age', 30)
        weight = user_data.get('weight', 70)
        height = user_data.get('height', 170)
        activity_level = user_data.get('activity_level', 'moderately_active')
        goal = user_data.get('goal', 'maintain')

        # Mifflin-St Jeor
        if sex == 'M':
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        multipliers = {
            'sedentary': 1.2,
            'lightly_active': 1.375,
            'moderately_active': 1.55,
            'very_active': 1.725,
            'extremely_active': 1.9
        }
        tdee = bmr * multipliers.get(activity_level, 1.55)

        adjustments = {
            'weight_loss': 0.85,
            'maintain': 1.0,
            'muscle_gain': 1.15
        }
        daily_cal = tdee * adjustments.get(goal, 1.0)

        # macro split (更靈活：可以依 goal 調整)
        if goal == 'weight_loss':
            prot_pct, carb_pct, fat_pct = 0.30, 0.40, 0.30
        elif goal == 'muscle_gain':
            prot_pct, carb_pct, fat_pct = 0.30, 0.50, 0.20
        else:
            prot_pct, carb_pct, fat_pct = 0.25, 0.50, 0.25

        protein_g = (daily_cal * prot_pct) / 4.0
        carbs_g = (daily_cal * carb_pct) / 4.0
        fats_g = (daily_cal * fat_pct) / 9.0

        return {
            'daily_calories': round(daily_cal, 1),
            'protein_g': round(protein_g, 1),
            'carbohydrates_g': round(carbs_g, 1),
            'fats_g': round(fats_g, 1),
            'fiber_g': user_data.get('fiber_g', 25),
            'tdee': round(tdee, 1),
            'bmr': round(bmr, 1)
        }

    # -----------------------
    # Recommendation logic
    # -----------------------
    def get_meal_recommendations(self,
                                 user_data: Dict[str, Any],
                                 meal_type: str = "lunch",
                                 max_recommendations: int = 6,
                                 preferences: Optional[List[str]] = None,
                                 exclude_types: Optional[List[str]] = None
                                 ) -> List[Dict[str, Any]]:
        """
        取得推薦食物清單
        user_data 必須包含 user_id （若你想讓系統使用 MealTracker 取得今日攝入）
        meal_type: breakfast/lunch/dinner/snack
        preferences: list of preferred food_type, e.g. ['protein', 'vegetable']
        exclude_types: list of food_type to避免
        """
        try:
            # 1) compute needs
            needs = self.calculate_user_needs(user_data)

            # 2) obtain today's intake (use meal_tracker if available)
            uid = user_data.get('user_id')
            if self.meal_tracker and uid is not None:
                today_intake = self.meal_tracker.get_today_intake(uid)
            else:
                # fallback: zeroed
                today_intake = {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0}

            # 3) remaining needs for this meal (allocation)
            allocations = {'breakfast': 0.25, 'lunch': 0.35, 'dinner': 0.30, 'snack': 0.10}
            alloc = allocations.get(meal_type, 0.3)
            remaining = {
                'calories': max(0.0, needs['daily_calories'] * alloc - today_intake.get('calories', 0.0)),
                'protein': max(0.0, needs['protein_g'] * alloc - today_intake.get('protein', 0.0)),
                'carbs': max(0.0, needs['carbohydrates_g'] * alloc - today_intake.get('carbs', 0.0)),
                'fats': max(0.0, needs['fats_g'] * alloc - today_intake.get('fats', 0.0))
            }

            # if remaining calories are near zero, return empty list
            if remaining['calories'] < 5:
                return []

            # 4) fetch candidate foods from DB and filter by meal_type semantics
            meal_filters = {
                'breakfast': ['grain', 'fruit', 'dairy'],
                'lunch': ['protein', 'vegetable', 'grain'],
                'dinner': ['protein', 'vegetable', 'grain'],
                'snack': ['fruit', 'nuts', 'dairy']
            }
            allowed_types = meal_filters.get(meal_type, None)

            with self._connect() as conn:
                cur = conn.cursor()
                if allowed_types:
                    q = f"SELECT * FROM food_nutrition WHERE food_type IN ({','.join('?' for _ in allowed_types)})"
                    cur.execute(q, allowed_types)
                else:
                    cur.execute("SELECT * FROM food_nutrition")
                rows = cur.fetchall()

            candidates = [dict(r) for r in rows]

            # apply excludes
            if exclude_types:
                candidates = [c for c in candidates if c.get('food_type') not in set(exclude_types)]

            # 5) score each candidate
            scored = []
            for food in candidates:
                # per 100g nutrition
                cal100 = float(food.get('calories') or 0.0)
                prot100 = float(food.get('protein') or 0.0)
                carb100 = float(food.get('carbohydrates') or 0.0)
                fat100 = float(food.get('fats') or 0.0)

                # if food has zero calories and no macros, skip
                if cal100 <= 0 and prot100 <= 0 and carb100 <= 0 and fat100 <= 0:
                    continue

                # estimate recommended grams to satisfy remaining calories
                rec_qty = self._calculate_recommended_quantity_from_remaining(cal100, remaining['calories'])

                # nutrition that rec_qty provides
                factor = rec_qty / 100.0
                provide = {
                    'calories': cal100 * factor,
                    'protein': prot100 * factor,
                    'carbs': carb100 * factor,
                    'fats': fat100 * factor
                }

                # score components (all normalized to 0..1)
                nutrition_score = self._nutrition_match_score(provide, remaining)
                goal_score = self._goal_alignment_score(food, needs, provide, user_data)
                preference_score = self._preference_score(food, user_data, preferences)
                diversity_score = 0.7  # placeholder; could use history to compute diversity

                total_score = (nutrition_score * 0.35 +
                               goal_score * 0.35 +
                               preference_score * 0.20 +
                               diversity_score * 0.10)

                scored.append({
                    'food_id': food.get('food_id'),
                    'food_name': food.get('food_name'),
                    'food_type': food.get('food_type'),
                    'per_100g': {'calories': cal100, 'protein': prot100, 'carbs': carb100, 'fats': fat100},
                    'recommended_quantity_g': rec_qty,
                    'provide': provide,
                    'score': round(total_score, 4),
                    'nutrition_score': round(nutrition_score, 4),
                    'goal_score': round(goal_score, 4),
                    'preference_score': round(preference_score, 4)
                })

            # sort and return top-N
            scored.sort(key=lambda x: x['score'], reverse=True)
            return scored[:max_recommendations]

        except Exception as ex:
            print(f"get_meal_recommendations error: {ex}")
            return []

    # -----------------------
    # Scoring helpers
    # -----------------------
    @staticmethod
    def _calculate_recommended_quantity_from_remaining(cal_per_100g: float, remaining_calories: float) -> int:
        """
        基於 remaining_calories 決定推薦攝取量（g）。
        - 若 cal_per_100g == 0，回傳 100g 的保守值
        - 限制於 30 - 500g，四捨五入到 5g
        """
        if cal_per_100g <= 0:
            base = 100.0
        else:
            base = (remaining_calories / cal_per_100g) * 100.0

        # clamp and round to nearest 5g
        base = max(30.0, min(500.0, base))
        return int(round(base / 5.0) * 5)

    @staticmethod
    def _nutrition_match_score(provide: Dict[str, float], remaining: Dict[str, float]) -> float:
        """
        計算營養匹配度：對每個 macro 計算 min(provide / remaining, 1)，再取加權平均。
        若 remaining 為 0，對應項視為 1（因為不需要該 macro）。
        回傳 0..1。
        """
        weights = {'calories': 0.4, 'protein': 0.3, 'carbs': 0.2, 'fats': 0.1}
        s = 0.0
        for k, w in weights.items():
            rem = remaining.get(k, 0.0)
            prov = provide.get(k, 0.0)
            if rem <= 0:
                ratio = 1.0
            else:
                ratio = min(prov / rem, 1.0)
            s += ratio * w
        return max(0.0, min(1.0, s))

    @staticmethod
    def _goal_alignment_score(food: Dict[str, Any], needs: Dict[str, float], provide: Dict[str, float], user_data: Dict[str, Any]) -> float:
        """
        根據用戶目標 (weight_loss/muscle_gain/maintain) 評估食物的對齊度。
        使用 protein-per-calorie 與 fiber/low-fat 特性來偏好減重或增肌。
        統一 normalize 到 0..1。
        """
        goal = user_data.get('goal', 'maintain')
        # avoid division by zero
        prov_cal = max(1e-6, provide.get('calories', 0.0))
        prot_per_100cal = (provide.get('protein', 0.0) / prov_cal) * 100.0  # g protein per 100 kcal

        # heuristics (可調)
        if goal == 'weight_loss':
            # prefer higher protein density and lower fat density
            prot_score = min(prot_per_100cal / 8.0, 1.0)  # ~8g/100kcal is very protein-dense
            fat_score = 1.0 - min((provide.get('fats', 0.0) / prov_cal) * 100.0 / 10.0, 1.0)
            return max(0.0, min(1.0, 0.7 * prot_score + 0.3 * fat_score))
        elif goal == 'muscle_gain':
            # prefer high protein and sufficient calories
            prot_score = min(prot_per_100cal / 10.0, 1.0)  # stricter
            cal_score = min(provide.get('calories', 0.0) / (needs['daily_calories'] * 0.2 + 1e-6), 1.0)
            return max(0.0, min(1.0, 0.6 * prot_score + 0.4 * cal_score))
        else:
            # maintain: prefer balanced
            # closeness to macro ratio (protein:carb:fat) as fraction of needs
            def ratio_score(key):
                need = {'protein': needs['protein_g'], 'carbs': needs['carbohydrates_g'], 'fats': needs['fats_g']}[key]
                if need <= 0:
                    return 1.0
                return min(provide.get(key, 0.0) / (need * 0.25 + 1e-6), 1.0)  # compare to meal allocation ~25%
            p = ratio_score('protein'); c = ratio_score('carbs'); f = ratio_score('fats')
            return (p + c + f) / 3.0

    @staticmethod
    def _preference_score(food: Dict[str, Any], user_data: Dict[str, Any], preferences: Optional[List[str]] = None) -> float:
        """
        若使用者提供 preferences（food_type 清單），則給予偏好加分；若沒有，使用簡單預設權重。
        回傳 0..1。
        """
        # explicit preferences override
        if preferences:
            return 1.0 if food.get('food_type') in set(preferences) else 0.4

        # fallback defaults
        type_pref = {
            'protein': 1.0,
            'vegetable': 0.9,
            'fruit': 0.8,
            'grain': 0.8,
            'dairy': 0.7,
            'nuts': 0.7
        }
        return float(type_pref.get(food.get('food_type'), 0.5))


# -----------------------
# Example usage
# -----------------------
if __name__ == "__main__":
    # 範例假設：已有 MealTracker，並同一個 DB file
    from meal_tracker import MealTracker  # 請確保 meal_tracker.py 可 import
    mt = MealTracker("test_mealtracker.db")
    rs = RecommendationService("test_mealtracker.db", meal_tracker=mt)

    user = {
        'user_id': 1,
        'sex': 'F',
        'age': 28,
        'weight': 58,
        'height': 162,
        'activity_level': 'moderately_active',
        'goal': 'muscle_gain'
    }

    recs = rs.get_meal_recommendations(user, meal_type='lunch', max_recommendations=5, preferences=['protein'])
    import pprint; pprint.pprint(recs)