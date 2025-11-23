from pathlib import Path
from models.user import User
from services.meal_tracker import MealTracker
from services.recommendation_service import RecommendationService
from decision_tree import DecisionTreeNutritionist
import sys

def _prompt_float(prompt_text: str) -> float:
    while True:
        try:
            return float(input(prompt_text))
        except ValueError:
            print("Invalid number, please try again.")

def main():
    print("Welcome to the AI Nutritionist App!")

    # safe input parsing
    height = _prompt_float("Enter your height in cm: ")
    weight = _prompt_float("Enter your current weight in kg: ")
    sex = input("Enter your sex (M/F): ").strip().upper()
    try:
        age = int(input("Enter your age in years: ").strip())
    except ValueError:
        print("Invalid age, exiting.")
        sys.exit(1)
    target_weight = _prompt_float("Enter your target weight in kg: ")

    user = User(
        height=height,
        weight=weight,
        sex=sex,
        age=age,
        target_weight=target_weight
    )

    # Use project-relative DB paths (run script from src or use absolute paths)
    BASE_DIR = Path(__file__).resolve().parent
    DB_PATH = str(BASE_DIR / "user_history.db")
    FOOD_DB = str(BASE_DIR / "food_nutrition.db")

    meal_tracker = MealTracker(DB_PATH)
    recommendation_service = RecommendationService(FOOD_DB)
    dt_nutritionist = DecisionTreeNutritionist(FOOD_DB)

    # train model but don't crash the app if training fails
    try:
        dt_nutritionist.train_model()
        trained_ok = True
    except Exception as e:
        print(f"Warning: Decision tree training failed: {e}. Falling back to simple rating.")
        trained_ok = False

    # meal logging loop
    while True:
        meal = input("Enter your meal (or type 'exit' to finish): ").strip()
        if meal.lower() == 'exit':
            break

        current_weight = _prompt_float("Enter your current weight in kg: ")

        try:
            meal_tracker.log_meal(user_id=1, meal_details=meal)
            meal_tracker.update_weight(user_id=1, new_weight=current_weight)
            print("Meal & weight updated!\n")
        except Exception as e:
            print(f"Failed to save meal/weight: {e}")

    print("Generating recommendations...\n")

    user_data = {"sex": sex, "age": age}
    rec_meals = recommendation_service.get_meal_recommendations(user_data)

    if not rec_meals:
        print("No recommendations found for your profile.")
        return

    print("Here are your meal recommendations:")
    for meal in rec_meals:
        # safely extract numeric nutrition values (may be stored as strings)
        def to_float_safe(x):
            try:
                return float(x)
            except (TypeError, ValueError):
                return None

        calories = to_float_safe(meal.get('calories'))
        protein = to_float_safe(meal.get('protein'))
        carbs = to_float_safe(meal.get('carbs'))
        fat = to_float_safe(meal.get('fat'))

        meal_nut = {"calories": calories, "protein": protein, "carbs": carbs, "fat": fat}

        # try model rating, otherwise fallback to RecommendationService.rate_meal (simple cal-based)
        try:
            rating = dt_nutritionist.rate_meal(meal_nut) if trained_ok else recommendation_service.rate_meal(meal_nut)
        except Exception:
            rating = recommendation_service.rate_meal(meal_nut)

        print(f"{meal.get('food_name','Unknown')} - {rating}")


if __name__ == "__main__":
    main()
