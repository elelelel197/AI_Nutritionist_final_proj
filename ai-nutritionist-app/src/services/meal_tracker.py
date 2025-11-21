from datetime import date, datetime, timedelta
import sqlite3
from typing import List, Dict, Optional, Any


class MealTracker:
    """
    改良版 MealTracker

    資料庫 schema:
    - food_nutrition: 存放食物營養（數值以 per_100g 為單位）
    - user_history: 記錄用戶餐食或體重更新（entry_type = 'meal' 或 'weight'）

    日期皆以 `YYYY-MM-DD`（ISO）字串存放。
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_tables()

    # -----------------------
    # Helpers / DB utilities
    # -----------------------
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        # 返回 row 可以用 dict-like 存取
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self) -> None:
        """建立必要的 table、index，以及設定 PRAGMA"""
        with self._connect() as conn:
            cur = conn.cursor()
            # PRAGMA 設定
            cur.execute("PRAGMA foreign_keys = ON;")
            cur.execute("PRAGMA journal_mode = WAL;")
            # food_nutrition: calories/protein/... 皆以 per_100g 為單位
            cur.execute('''
                CREATE TABLE IF NOT EXISTS food_nutrition (
                    food_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    food_name TEXT NOT NULL,
                    food_type TEXT,
                    calories REAL DEFAULT 0,        -- per 100g
                    protein REAL DEFAULT 0,         -- per 100g
                    carbohydrates REAL DEFAULT 0,   -- per 100g
                    fats REAL DEFAULT 0,            -- per 100g
                    vitamins TEXT,
                    minerals TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # user_history: 支援 meal / weight 兩類 entry
            cur.execute('''
                CREATE TABLE IF NOT EXISTS user_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,                        -- ISO YYYY-MM-DD
                    entry_type TEXT NOT NULL DEFAULT 'meal',   -- 'meal' or 'weight'
                    meal_consumed TEXT,                        -- 描述 (comma separated)
                    calories_consumed REAL,
                    protein_consumed REAL,
                    carbs_consumed REAL,
                    fats_consumed REAL,
                    current_weight REAL,                       -- kg (only for entry_type='weight')
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 索引
            cur.execute('CREATE INDEX IF NOT EXISTS idx_food_type ON food_nutrition(food_type);')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_user_date ON user_history(user_id, date);')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_user_entry_date ON user_history(user_id, entry_type, date);')
            conn.commit()

    # -----------------------
    # Food table helpers
    # -----------------------
    def add_food_item(self, food_name: str, food_type: str = None,
                      calories_per_100g: float = 0, protein_per_100g: float = 0,
                      carbs_per_100g: float = 0, fats_per_100g: float = 0,
                      vitamins: str = None, minerals: str = None) -> int:
        """
        新增食物到 food_nutrition，回傳 food_id
        values are per 100g
        """
        if not food_name:
            raise ValueError("food_name 必須提供")
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO food_nutrition
                (food_name, food_type, calories, protein, carbohydrates, fats, vitamins, minerals)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (food_name, food_type, calories_per_100g, protein_per_100g,
                  carbs_per_100g, fats_per_100g, vitamins, minerals))
            return cur.lastrowid

    def get_food_by_id(self, food_id: int) -> Optional[Dict[str, Any]]:
        """取得指定 food_id 的食物資料（或 None）"""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM food_nutrition WHERE food_id = ?', (food_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    # -----------------------
    # Logging meals & weight
    # -----------------------
    def log_meal(self, user_id: int, food_id: int, quantity_g: float = 100.0,
                 notes: str = None) -> bool:
        """
        記錄單一食物作為一餐（或餐的一部分）
        quantity_g: 食物重量（克），對應 food_nutrition 的 per_100g 值
        """
        if user_id <= 0:
            raise ValueError("user_id 必須為正整數")
        if quantity_g <= 0:
            raise ValueError("quantity_g 必須大於 0")

        food = self.get_food_by_id(food_id)
        if not food:
            raise ValueError(f"food_id {food_id} 不存在")

        factor = quantity_g / 100.0
        calories = (food.get('calories') or 0.0) * factor
        protein = (food.get('protein') or 0.0) * factor
        carbs = (food.get('carbohydrates') or 0.0) * factor
        fats = (food.get('fats') or 0.0) * factor
        meal_desc = f"{food.get('food_name')}({quantity_g}g)"

        today = date.today().isoformat()
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO user_history
                (user_id, date, entry_type, meal_consumed, calories_consumed, protein_consumed, carbs_consumed, fats_consumed, notes)
                VALUES (?, ?, 'meal', ?, ?, ?, ?, ?, ?)
            ''', (user_id, today, meal_desc, calories, protein, carbs, fats, notes))
            return True

    def log_meal_with_details(self, user_id: int, meal_details: Dict) -> bool:
        """
        記錄包含多個食物或自定義食物的完整餐食。
        meal_details 範例:
        {
            'foods': [{'food_id': 1, 'quantity': 150}, ...],
            'custom_food': '自定義食物名稱',  # 可選
            'custom_calories': 200,          # 可選 (直接加入卡路里)
            'notes': '備註'
        }
        """
        if user_id <= 0:
            raise ValueError("user_id 必須為正整數")

        foods = meal_details.get('foods', []) or []
        custom_food = meal_details.get('custom_food')
        custom_calories = float(meal_details.get('custom_calories', 0) or 0)
        notes = meal_details.get('notes')

        total_cal = total_pro = total_carbs = total_fats = 0.0
        names = []

        with self._connect() as conn:
            cur = conn.cursor()
            for item in foods:
                fid = int(item.get('food_id'))
                qty = float(item.get('quantity', 100))
                food = self.get_food_by_id(fid)
                if not food:
                    # 跳過不存在的食物
                    continue
                factor = qty / 100.0
                total_cal += (food.get('calories') or 0.0) * factor
                total_pro += (food.get('protein') or 0.0) * factor
                total_carbs += (food.get('carbohydrates') or 0.0) * factor
                total_fats += (food.get('fats') or 0.0) * factor
                names.append(f"{food.get('food_name')}({int(qty)}g)")

            if custom_food:
                names.append(custom_food)
                total_cal += custom_calories

            meal_description = ", ".join(names)
            if notes:
                meal_description = f"{meal_description} - {notes}" if meal_description else notes

            today = date.today().isoformat()
            cur.execute('''
                INSERT INTO user_history
                (user_id, date, entry_type, meal_consumed, calories_consumed, protein_consumed, carbs_consumed, fats_consumed, notes)
                VALUES (?, ?, 'meal', ?, ?, ?, ?, ?, ?)
            ''', (user_id, today, meal_description, total_cal, total_pro, total_carbs, total_fats, notes))
            return True

    def update_weight(self, user_id: int, new_weight_kg: float, notes: str = None) -> bool:
        """
        新增一筆體重紀錄（entry_type='weight'）
        """
        if user_id <= 0:
            raise ValueError("user_id 必須為正整數")
        if new_weight_kg <= 0:
            raise ValueError("new_weight_kg 必須大於 0")

        today = date.today().isoformat()
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO user_history
                (user_id, date, entry_type, current_weight, notes)
                VALUES (?, ?, 'weight', ?, ?)
            ''', (user_id, today, new_weight_kg, notes))
            return True

    # -----------------------
    # Queries / summaries
    # -----------------------
    def get_meal_history(self, user_id: int, days: int = 7) -> List[Dict]:
        """
        取得最近 `days` 天的餐食紀錄（包含當日）。
        days >= 1
        """
        if days < 1:
            raise ValueError("days 必須 >= 1")
        start_date = (date.today() - timedelta(days=days - 1)).isoformat()  # 包含當日
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT date, meal_consumed, calories_consumed, protein_consumed, carbs_consumed, fats_consumed, notes
                FROM user_history
                WHERE user_id = ? AND entry_type = 'meal' AND date >= ?
                ORDER BY date DESC, id DESC
            ''', (user_id, start_date))
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def get_daily_summary(self, user_id: int, target_date: Optional[str] = None) -> Dict[str, Any]:
        """
        取得指定日期的營養摘要（YYYY-MM-DD），預設為今天
        回傳 keys: date, total_calories, total_protein, total_carbs, total_fats
        """
        if target_date is None:
            target_date = date.today().isoformat()

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT 
                    COALESCE(SUM(calories_consumed), 0) as total_calories,
                    COALESCE(SUM(protein_consumed), 0) as total_protein,
                    COALESCE(SUM(carbs_consumed), 0) as total_carbs,
                    COALESCE(SUM(fats_consumed), 0) as total_fats
                FROM user_history
                WHERE user_id = ? AND entry_type = 'meal' AND date = ?
            ''', (user_id, target_date))
            row = cur.fetchone()
            return {
                'date': target_date,
                'total_calories': row['total_calories'],
                'total_protein': row['total_protein'],
                'total_carbs': row['total_carbs'],
                'total_fats': row['total_fats']
            }

    def get_current_weight(self, user_id: int) -> Optional[float]:
        """
        取得最近一筆體重紀錄（依 date, id 排序），若沒有則回傳 None
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT current_weight FROM user_history
                WHERE user_id = ? AND entry_type = 'weight' AND current_weight IS NOT NULL
                ORDER BY date DESC, id DESC
                LIMIT 1
            ''', (user_id,))
            row = cur.fetchone()
            return float(row['current_weight']) if row else None

    def get_weight_history(self, user_id: int, days: int = 30) -> List[Dict]:
        """
        取得最近 `days` 天的體重紀錄（包含當日）
        """
        if days < 1:
            raise ValueError("days 必須 >= 1")
        start_date = (date.today() - timedelta(days=days - 1)).isoformat()
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT date, current_weight, notes
                FROM user_history
                WHERE user_id = ? AND entry_type = 'weight' AND date >= ?
                ORDER BY date ASC
            ''', (user_id, start_date))
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    # -----------------------
    # Utility: today intake (for recommendation service)
    # -----------------------
    def get_today_intake(self, user_id: int) -> Dict[str, float]:
        """
        取得 user 今日已攝入的營養總和（以 YYYY-MM-DD 計）
        返回 dict: calories, protein, carbs, fats
        """
        today = date.today().isoformat()
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT
                    COALESCE(SUM(calories_consumed), 0) AS total_calories,
                    COALESCE(SUM(protein_consumed), 0)  AS total_protein,
                    COALESCE(SUM(carbs_consumed), 0)    AS total_carbs,
                    COALESCE(SUM(fats_consumed), 0)    AS total_fats
                FROM user_history
                WHERE user_id = ? AND entry_type = 'meal' AND date = ?
            ''', (user_id, today))
            row = cur.fetchone()
            return {
                'calories': row['total_calories'],
                'protein': row['total_protein'],
                'carbs': row['total_carbs'],
                'fats': row['total_fats']
            }

    # -----------------------
    # Misc
    # -----------------------
    def delete_all_data_for_user(self, user_id: int) -> None:
        """測試用：刪除某 user 的所有紀錄（慎用）"""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('DELETE FROM user_history WHERE user_id = ?', (user_id,))
            conn.commit()

    def close(self):
        """便於 API 兼容：sqlite 使用 context manager 故不保留長期連線。"""
        pass


# -----------------------
# 範例使用（可刪除）
# -----------------------
if __name__ == "__main__":
    mt = MealTracker("test_mealtracker.db")
    # 新增示範食物（每100g）
    chicken_id = mt.add_food_item("雞胸肉(熟)", "protein", calories_per_100g=165, protein_per_100g=31, carbs_per_100g=0, fats_per_100g=3.6)
    rice_id = mt.add_food_item("白飯", "grain", calories_per_100g=130, protein_per_100g=2.4, carbs_per_100g=28, fats_per_100g=0.3)

    # 記錄餐食
    mt.log_meal(1, chicken_id, 150)   # 150g 雞胸肉
    mt.log_meal_with_details(1, {"foods": [{"food_id": rice_id, "quantity": 200}], "notes": "午餐"})

    # 更新體重
    mt.update_weight(1, 62.3, notes="晨測")

    print("今日摘要:", mt.get_daily_summary(1))
    print("今日已攝入:", mt.get_today_intake(1))
    print("最近體重:", mt.get_current_weight(1))
