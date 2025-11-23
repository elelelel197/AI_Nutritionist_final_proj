from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
import pandas as pd
import sqlite3
from typing import Optional, Dict, Any, List
import numpy as np

class DecisionTreeNutritionist:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.model = DecisionTreeClassifier()
        self.label_encoder: Optional[LabelEncoder] = None
        self.imputer = SimpleImputer(strategy="mean")
        self.food_data = self.load_food_data()
        self.recommended_intake = self.load_recommended_intake()
        self._is_trained = False

    def load_food_data(self) -> pd.DataFrame:
        conn = sqlite3.connect(self.db_path)
        try:
            query = "SELECT * FROM food_nutrition"
            df = pd.read_sql_query(query, conn)
        finally:
            conn.close()
        return df

    def load_recommended_intake(self) -> pd.DataFrame:
        conn = sqlite3.connect(self.db_path)
        try:
            query = "SELECT * FROM recommended_intake"
            df = pd.read_sql_query(query, conn)
        finally:
            conn.close()
        return df

    def train_model(self) -> None:
        required = {'calories', 'protein', 'carbs', 'fat', 'rating'}
        if self.food_data is None or not required.issubset(set(self.food_data.columns)):
            raise RuntimeError(f"food_nutrition must contain columns: {required}")

        features = ['calories', 'protein', 'carbs', 'fat']
        X = self.food_data[features].apply(pd.to_numeric, errors='coerce')
        X_imputed = self.imputer.fit_transform(X)

        y = self.food_data['rating']
        # encode labels if non-numeric / categorical
        if y.dtype == object or y.dtype.name == 'category':
            self.label_encoder = LabelEncoder()
            y_enc = self.label_encoder.fit_transform(y.astype(str))
        else:
            y_enc = pd.to_numeric(y, errors='coerce')
            if np.isnan(y_enc).any():
                self.label_encoder = LabelEncoder()
                y_enc = self.label_encoder.fit_transform(y.astype(str))

        self.model.fit(X_imputed, y_enc)
        self._is_trained = True

    def rate_meal(self, meal_nutrition: Dict[str, Any]):
        if not self._is_trained:
            raise RuntimeError("Model is not trained. Call train_model() before rate_meal().")

        features = ['calories', 'protein', 'carbs', 'fat']
        vals = []
        for k in features:
            try:
                vals.append(float(meal_nutrition.get(k)))
            except (TypeError, ValueError):
                vals.append(np.nan)
        X = self.imputer.transform([vals])
        pred = self.model.predict(X)[0]
        if self.label_encoder is not None:
            return self.label_encoder.inverse_transform([int(pred)])[0]
        return int(pred) if isinstance(pred, (np.integer, int)) else pred

    def get_user_recommended_intake(self, sex, age):
        df = self.recommended_intake
        result = df[(df['sex'] == sex) & (df['age'] == age)]
        if result.empty:
            return None
        return result.iloc[0]

    def recommend_meal(self, user_data: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        # try explicit caloric_needs first
        cal_need = None
        if 'caloric_needs' in user_data:
            try:
                cal_need = float(user_data['caloric_needs'])
            except (TypeError, ValueError):
                cal_need = None

        if cal_need is None and {'sex', 'age'}.issubset(user_data):
            rec = self.get_user_recommended_intake(user_data['sex'], user_data['age'])
            if rec is not None and 'calories' in rec:
                try:
                    cal_need = float(rec['calories'])
                except (TypeError, ValueError):
                    cal_need = None

        if cal_need is None:
            raise RuntimeError("caloric_needs not provided and no matching recommended_intake found.")

        df = self.food_data.copy()
        df['calories'] = pd.to_numeric(df.get('calories', pd.Series(dtype=float)), errors='coerce')

        # predicted rating if model trained, else fallback to existing rating or neutral
        if self._is_trained:
            X = df[['calories', 'protein', 'carbs', 'fat']].apply(pd.to_numeric, errors='coerce')
            X_imputed = self.imputer.transform(X)
            preds = self.model.predict(X_imputed)
            if self.label_encoder is not None:
                df['predicted_rating'] = self.label_encoder.inverse_transform([int(p) for p in preds])
            else:
                df['predicted_rating'] = preds
        else:
            df['predicted_rating'] = df['rating'] if 'rating' in df.columns else 0

        goal = user_data.get("goal", "healthy")

        if goal == "lose_weight":
            df = df[df['calories'] <= cal_need]
            df = df.sort_values(by=['predicted_rating', 'protein', 'calories'],
                                ascending=[False, False, True], na_position='last')
        elif goal == "gain_muscle":
            df = df.sort_values(by=['protein', 'predicted_rating'],
                                ascending=[False, False], na_position='last')
        else:
            df = df.sort_values(by=['predicted_rating'], ascending=False, na_position='last')

        # determine output food name column
        name_col = next((c for c in ['food_name', 'name', 'title', 'food'] if c in df.columns), None)
        out_cols = ([name_col] if name_col else []) + [c for c in ['calories', 'protein', 'carbs', 'fat', 'predicted_rating'] if c in df.columns]

        result = df[out_cols].head(top_k).copy()
        if name_col and name_col != 'food_name':
            result = result.rename(columns={name_col: 'food_name'})
        if not name_col:
            result.insert(0, 'food_name', [''] * len(result))

        return result.to_dict(orient='records')
