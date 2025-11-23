CREATE TABLE users_preference(
    user_id TEXT NOT NULL, 
    food_types TEXT NOT NULL, 
    food_names TEXT NOT NULL, 
    food_preferences FLOAT NOT NULL
    );

CREATE TABLE users_activity_level(
    user_id TEXT NOT NULL, 
    activity_level TEXT NOT NULL
    );