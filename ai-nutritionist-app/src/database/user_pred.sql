CREATE TABLE users_preference(
    user_id TEXT NOT NULL, 
    food_type TEXT NOT NULL, 
    food_name TEXT NOT NULL, 
    food_preference FLOAT NOT NULL
    );

CREATE TABLE users_activity_level(
    user_id TEXT NOT NULL, 
    activity_level TEXT NOT NULL
    );

CREATE TABLE user_weight_gain_loss_factor(
    user_id TEXT NOT NULL, 
    weight_gain_factor FLOAT NOT NULL,
    weight_loss_factor FLOAT NOT NULL
    );