def calculate_bmi(weight, height):
    if height <= 0:
        raise ValueError("Height must be greater than zero.")
    return weight / (height ** 2)

def convert_to_kilograms(pounds):
    return pounds * 0.453592

def convert_to_centimeters(feet, inches):
    return (feet * 12 + inches) * 2.54

def validate_user_input(height, weight, age, target_weight):
    if height <= 0:
        raise ValueError("Height must be greater than zero.")
    if weight <= 0:
        raise ValueError("Weight must be greater than zero.")
    if age <= 0:
        raise ValueError("Age must be greater than zero.")
    if target_weight <= 0:
        raise ValueError("Target weight must be greater than zero.")

def calculate_caloric_gain_loss_to_weight_change(caloric_gain_loss: float):
    # Approximately 7700 calories lead to 1 kg of weight gain
    return caloric_gain_loss / 7700

def calculate_daily_caloric_needs(weight, height, age, sex, activity_level):
    if sex not in ['male', 'female']:
        raise ValueError("Sex must be 'male' or 'female'.")
    
    if sex == 'male':
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