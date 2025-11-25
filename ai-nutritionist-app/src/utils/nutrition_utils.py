def calculate_bmi(weight, height):
    if height <= 0:
        raise ValueError("Height must be greater than zero.")
    return weight / (height ** 2)

def convert_to_kilograms(pounds):
    return pounds * 0.453592

def convert_to_centimeters(feet, inches):
    return (feet * 12 + inches) * 2.54

def calculate_caloric_gain_loss_to_weight_change(caloric_gain_loss: float):
    # Approximately 7700 calories lead to 1 kg of weight gain
    return caloric_gain_loss / 7700

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
    
    protein_g = (daily_calories * protein_pct) / 4
    carbs_g = (daily_calories * carb_pct) / 4
    fats_g = (daily_calories * fat_pct) / 9
    
    return {
        'daily_calories': round(daily_calories, 1),
        'protein_g': round(protein_g, 1),
        'carbohydrates_g': round(carbs_g, 1),
        'fats_g': round(fats_g, 1),
    }

def get_healthy_nutrition_composition(food_type):
    healthy_nutrition_composition = {
        'grains':    {'carbs': 70, 'protein': 10, 'fats': 2},    # per 100g
        'protein':   {'carbs': 0,  'protein': 20, 'fats': 5},
        'vegetable': {'carbs': 5,  'protein': 2,  'fats': 0.5},
        'fruit':     {'carbs': 15, 'protein': 1,  'fats': 0.2},
        'oil':       {'carbs': 20,  'protein': 20,  'fats': 50},
        'dairy':     {'carbs': 5,  'protein': 3.5,'fats': 2}
    }
    return healthy_nutrition_composition.get(food_type, None)