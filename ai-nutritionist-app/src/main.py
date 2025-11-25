# ai-nutritionist-app/src/main.py
from models.user import User
from models.meal import Meal
from services.auth_service import AuthService
from services.recommendation_service import RecommendationService

def main():

    while True:
        print("Welcome to the AI Nutritionist App!")
        print("Press 0 to login")
        print("Press 1 to sign up")

        user = None
        command = input()
        if command:
            # sign up
            id = str(input("Enter your desired id"))
            height = float(input("Enter your height in cm: "))
            weight = float(input("Enter your current weight in kg: "))
            sex = input("Enter your sex (M/F): ").upper()
            age = int(input("Enter your age in years: "))
            estimated_time = int(input("Enter your time to reach the goal in days: "))
            target_weight = float(input("Enter your target weight in kg: "))
            user = AuthService.
        # User input for personal details
        
    
    # Initialize user model
    from models.user import User
    user = User(height, weight, sex, age, target_weight)
    
    # Meal tracking
    from services.meal_tracker import MealTracker
    meal_tracker = MealTracker(user)
    
    while True:
        meal = input("Enter your meal (or type 'exit' to finish): ")
        if meal.lower() == 'exit':
            break
        current_weight = float(input("Enter your current weight in kg: "))
        meal_tracker.track_meal(meal, current_weight)
    
    # Recommendations
    from services.recommendation_service import RecommendationService
    recommendation_service = RecommendationService(user)
    recommendations = recommendation_service.get_recommendations()
    
    print("Here are your meal recommendations:")
    for recommendation in recommendations:
        print(recommendation)

if __name__ == "__main__":
    main()