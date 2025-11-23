CREATE TABLE users (
    user_id TEXT NOT NULL,
    height FLOAT, 
    weight FLOAT, 
    sex TEXT, 
    age INTEGER, 
    estimated_time INTEGER, 
    target_weight FLOAT,
    PRIMARY KEY (user_id, date),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE meals_log (
    user_id TEXT NOT NULL, 
    food_name TEXT NOT NULL, 
    quantity FLOAT, 
    meal_time DATE,
);

CREATE TABLE weight_log (
    user_id TEXT NOT NULL, 
    weight FLOAT NOT NULL, 
    log_time DATE,
);