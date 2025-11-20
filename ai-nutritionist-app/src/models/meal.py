class Meal:
    def __init__(self, food_items_quantity, time):
        # list of food items and quantity(in grams) in the meal
        self.food_items_quantity = food_items_quantity  # e.g., {'apple': 150, 'chicken_breast': 200} 
        self.time = time  # e.g., 'breakfast', 'lunch', 'dinner'
        self.calories = self.calculate_calories()
        self.protein = self.calculate_protein()
        self.carbs = self.calculate_carbs()
        self.fats = self.calculate_fats()

    @property
    def calculate_nutritional_values(self):
        
        return {
            'calories': self.calories,
            'protein': self.protein,
            'carbs': self.carbs,
            'fats': self.fats
        }

    def __str__(self):
        return f"{self.name}: {self.calculate_nutritional_values()}"