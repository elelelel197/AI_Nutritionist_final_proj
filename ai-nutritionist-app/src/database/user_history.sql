CREATE TABLE user_history (
    user_id INTEGER NOT NULL,
    date DATE NOT NULL,
    current_weight FLOAT NOT NULL,
    meal_consumed TEXT NOT NULL,
    calories_consumed FLOAT NOT NULL,
    PRIMARY KEY (user_id, date),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);