class NutritionUtils:
    @staticmethod
    def calculate_bmi(weight, height):
        if height <= 0:
            raise ValueError("Height must be greater than zero.")
        return weight / (height ** 2)

    @staticmethod
    def convert_to_kilograms(pounds):
        return pounds * 0.453592

    @staticmethod
    def convert_to_centimeters(feet, inches):
        return (feet * 12 + inches) * 2.54

    @staticmethod
    def calculate_caloric_gain_loss_to_weight_change(caloric_gain_loss: float):
        # Approximately 7700 calories lead to 1 kg of weight gain
        return caloric_gain_loss / 7700

    @staticmethod
    def calculate_daily_caloric_needs(weight, height, age, sex, activity_level):
        if sex not in ['M', 'F']:
            raise ValueError("Sex must be 'M' or 'F'.")
        
        if sex == 'M':
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
        activity_multiplier = {
            'sedentary': 1.2,
            'lightly active': 1.375,
            'moderately active': 1.55,
            'very active': 1.725,
            'super active': 1.9
        }
        
        return bmr * activity_multiplier.get(activity_level, 1.2)

    @staticmethod
    def calculate_macronutrient_distribution(daily_calories, current_weight, target_weight):
        if target_weight < current_weight:
            # Weight loss
            protein_pct, carb_pct, fat_pct = 0.30, 0.40, 0.30
        elif target_weight > current_weight:
            # Weight gain
            protein_pct, carb_pct, fat_pct = 0.30, 0.50, 0.20
        else:
            # Maintenance
            protein_pct, carb_pct, fat_pct = 0.25, 0.50, 0.25
        
        protein_100g = (daily_calories * protein_pct) / 4 * 100
        carbohydrates_100g = (daily_calories * carb_pct) / 4 * 100
        fats_100g = (daily_calories * fat_pct) / 9 * 100

        return {
            'calories': round(daily_calories, 1),
            'protein': round(protein_100g, 1),
            'carbohydrates': round(carbohydrates_100g, 1),
            'fats': round(fats_100g, 1),
        }

    @staticmethod
    def get_healthy_nutrition_composition(food_type) -> dict:
        healthy_nutrition_composition = {
            'grains':    {'calories': 82, 'protein': 10, 'carbohydrates': 70, 'fats': 2},    # per 100g
            'protein':   {'calories': 25,  'protein': 20, 'carbohydrates': 0, 'fats': 5},
            'vegetable': {'calories': 5,  'protein': 2,  'carbohydrates': 5, 'fats': 0.5},
            'fruit':     {'calories': 15, 'protein': 1,  'carbohydrates': 15, 'fats': 0.2},
            'oil':       {'calories': 90,  'protein': 20,  'carbohydrates': 20, 'fats': 50},
            'dairy':     {'calories': 10,  'protein': 3.5,'carbohydrates': 5, 'fats': 2}
        }
        return healthy_nutrition_composition.get(food_type, None)