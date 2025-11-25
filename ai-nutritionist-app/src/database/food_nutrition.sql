CREATE TABLE food_nutrition (
    food_type TEXT NOT NULL,
    food_name TEXT NOT NULL,
    calories FLOAT NOT NULL,
    protein FLOAT NOT NULL,
    carbohydrates FLOAT NOT NULL,
    fats FLOAT NOT NULL,
    vitamins TEXT,
    minerals TEXT,
)

INSERT INTO food_nutrition (food_type, food_name, calories, protein, carbohydrates, fats, vitamins, minerals) VALUES
('fruit', 'Apple', 52, 0.3, 14, 0.2, 'Vitamin C', 'Potassium'),
('fruit', 'Banana', 89, 1.1, 23, 0.3, 'Vitamin B6', 'Magnesium'),
('protein', 'Chicken Breast', 165, 31, 0, 3.6, 'Niacin', 'Phosphorus'),
('vegetable','Broccoli', 55, 3.7, 11, 0.6, 'Vitamin K', 'Calcium'),
('grains', 'Rice', 130, 2.7, 28, 0.3, 'Thiamine', 'Selenium'),
('protein', 'Salmon', 206, 22, 0, 13, 'Vitamin D', 'Selenium'),
('protein', 'Egg', 155, 13, 1.1, 11, 'Vitamin B12', 'Selenium'),
('oil', 'Almonds', 576, 21, 22, 49, 'Vitamin E', 'Magnesium'),
('grains', 'Oats', 389, 16.9, 66.3, 6.9, 'Thiamine', 'Iron'),
('vegetable', 'Spinach', 23, 2.9, 3.6, 0.4, 'Vitamin A', 'Iron');