class Meal:
    def __init__(self, name, calories, protein, carbs, fats):
        self.name = name
        self.calories = calories
        self.protein = protein
        self.carbs = carbs
        self.fats = fats

    def calculate_nutritional_values(self):
        return {
            'calories': self.calories,
            'protein': self.protein,
            'carbs': self.carbs,
            'fats': self.fats
        }

    def __str__(self):
        return f"{self.name}: {self.calculate_nutritional_values()}"