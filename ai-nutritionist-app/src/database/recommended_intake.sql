CREATE TABLE recommended_intake (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sex TEXT NOT NULL,
    age INTEGER NOT NULL,
    weight REAL NOT NULL,
    target_weight REAL NOT NULL,
    daily_calories REAL NOT NULL,
    protein REAL NOT NULL,
    carbohydrates REAL NOT NULL,
    fats REAL NOT NULL,
    fiber REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);