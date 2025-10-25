# ai-nutritionist-app/src/main.py

def main():
    print("Welcome to the AI Nutritionist App!")
    
    # User input for personal details
    height = float(input("Enter your height in cm: "))
    weight = float(input("Enter your current weight in kg: "))
    sex = input("Enter your sex (M/F): ").upper()
    age = int(input("Enter your age in years: "))
    target_weight = float(input("Enter your target weight in kg: "))
    
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