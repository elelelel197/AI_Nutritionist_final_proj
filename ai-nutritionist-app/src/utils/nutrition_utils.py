from typing import Union

def _normalize_sex(sex: str) -> str:
    if not isinstance(sex, str):
        raise ValueError("Sex must be a string.")
    s = sex.strip().lower()
    if s in ('m', 'male'):
        return 'male'
    if s in ('f', 'female'):
        return 'female'
    raise ValueError("Sex must be 'male'/'female' or 'M'/'F'.")

def calculate_bmi(weight: Union[int, float], height_cm: Union[int, float]) -> flo
   # 計算 BMI，height_cm（公分）會自動轉換成公尺。

    if height_cm is None or weight is None:
        raise ValueError("Weight and height must be provided.")
    if height_cm <= 0:
        raise ValueError("Height must be greater than zero.")
    height_m = float(height_cm) / 100.0
    return float(weight) / (height_m ** 2)


def calculate_bmi_category(bmi: Union[int, float]) -> str:
  
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 24.9:
        return "Normal"
    elif bmi < 29.9:
        return "Overweight"
    else:
        return "Obese"


def convert_to_kilograms(pounds: Union[int, float]) -> float:
  #p,kg
    return float(pounds) * 0.453592


def convert_to_centimeters(feet: Union[int, float], inches: Union[int, float]) -> float:
    
    return float(feet * 12 + inches) * 2.54


def validate_user_input(height: Union[int, float], weight: Union[int, float], age: int, target_weight: Union[int, float]) -> None:
   
    if height is None or height <= 0:
        raise ValueError("Height must be greater than zero.")
    if weight is None or weight <= 0:
        raise ValueError("Weight must be greater than zero.")
    if age is None or age <= 0:
        raise ValueError("Age must be greater than zero.")
    if target_weight is None or target_weight <= 0:
        raise ValueError("Target weight must be greater than zero.")


def calculate_daily_caloric_needs(weight: Union[int, float], height_cm: Union[int, float], age: int, sex: str, activity_level: str) -> float:
   
    sex_norm = _normalize_sex(sex)

    if sex_norm == 'male':
        bmr = 10 * float(weight) + 6.25 * float(height_cm) - 5 * int(age) + 5
    else:
        bmr = 10 * float(weight) + 6.25 * float(height_cm) - 5 * int(age) - 161

    # 支援常見別名
    activity_multiplier = {
        'sedentary': 1.2,
        'seden': 1.2,
        'lightly active': 1.375,
        'light': 1.375,
        'moderately active': 1.55,
        'moderate': 1.55,
        'very active': 1.725,
        'very': 1.725,
        'super active': 1.9,
        'super': 1.9
    }

    if not isinstance(activity_level, str):
        raise ValueError("activity_level must be a string describing activity (e.g. 'sedentary').")

    key = activity_level.strip().lower()
    if key not in activity_multiplier:
        raise ValueError(f"Invalid activity level: {activity_level}")

    return float(bmr * activity_multiplier[key])


def calculate_caloric_gain_loss_to_weight_change(total_caloric_difference: Union[int, float]) -> float:
    
    return float(total_caloric_difference) / 7700.0
