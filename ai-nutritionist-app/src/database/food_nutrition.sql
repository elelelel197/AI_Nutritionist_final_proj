CREATE TABLE food_nutrition (
    food_id INTEGER PRIMARY KEY,
    food_type TEXT NOT NULL,
    food_name TEXT NOT NULL,
    calories FLOAT NOT NULL,
    protein FLOAT NOT NULL,
    carbohydrates FLOAT NOT NULL,
    fats FLOAT NOT NULL,
    vitamins TEXT,
    minerals TEXT,
);

INSERT INTO food_nutrition (food_id, food_type, food_name, calories, protein, carbohydrates, fats, vitamins, minerals) VALUES
(1, 'fruit', 'Apple', 52, 0.3, 14, 0.2, 'Vitamin C', 'Potassium'),
(2, 'fruit', 'Banana', 89, 1.1, 23, 0.3, 'Vitamin B6', 'Magnesium'),
(3, 'protein', 'Chicken Breast', 165, 31, 0, 3.6, 'Niacin', 'Phosphorus'),
(4, 'vegetable','Broccoli', 55, 3.7, 11, 0.6, 'Vitamin K', 'Calcium'),
(5, 'grain', 'Rice', 130, 2.7, 28, 0.3, 'Thiamine', 'Selenium'),
(6, 'protein', 'Salmon', 206, 22, 0, 13, 'Vitamin D', 'Selenium'),
(7, 'protein', 'Egg', 155, 13, 1.1, 11, 'Vitamin B12', 'Selenium'),
(8, 'oil', 'Almonds', 576, 21, 22, 49, 'Vitamin E', 'Magnesium'),
(9, 'grains', 'Oats', 389, 16.9, 66.3, 6.9, 'Thiamine', 'Iron'),
(10, 'vegetable', 'Spinach', 23, 2.9, 3.6, 0.4, 'Vitamin A', 'Iron');