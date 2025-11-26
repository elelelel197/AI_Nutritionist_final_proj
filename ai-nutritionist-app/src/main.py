# ai-nutritionist-app/src/main.py
from models.user import User
from models.meal import Meal
from services.auth_service import AuthService
from services.recommendation_service import RecommendationService
from datetime import date
import pandas as pd
from algorithms.preference_algo import PreferenceAlgo
from algorithms.activity_lv_algo import ActivityLvAlgo
from algorithms.weight_g_l_algo import WeightGLAlgo
import utils.file_paths as fp

def main():

    while True:
        print("----------------------------------------")
        print("Welcome to the AI Nutritionist App!")
        print("Press 0 to login")
        print("Press 1 to sign up")
        print("Press 2 to exit")
        print("----------------------------------------")

        command = input("Enter your command: ")
        user = None
        time = date.today()
        match command:
            case '0':
                user_id = input("Enter your user ID: ")
                user = AuthService.user_login(user_id)
                if not user:
                    continue
            case '1':
                if AuthService.is_max_users_reached():
                    print("Maximum number of users reached. Cannot register new users.")
                    continue
                user_id = input("Choose a user ID: ")
                height = float(input("Enter your height in cm: "))
                weight = float(input("Enter your weight in kg: "))
                sex = input("Enter your sex (M/F): ").upper()
                age = int(input("Enter your age in years: "))
                estimated_days = int(input("Enter your estimated days to reach target weight in 'F's: "))
                target_weight = float(input("Enter your target weight in kg: "))

                user = AuthService.user_register(user_id, height, weight, sex, age, estimated_days, target_weight, time)
                if not user:
                    continue
            case '2':
                print("Exiting the AI Nutritionist App")
                break
            case _:
                print("Invalid command. Please try again.")
                continue
        
        while True:
            print("----------------------------------------")
            print(f"Welcome, {user.id}!")
            print("Press 0 to get a meal recommendation")
            print("Press 1 to log a meal")
            print("Press 2 to add food items to database")
            print("Press 3 to update weight")
            print("Press 4 to update user info")
            print("Press 5 to update user goal")
            print("Press 6 to logout")
            print("Press 7 to delete your account")
            print("----------------------------------------")
            command = input("Enter your command: ")
            match command:
                # Get meal recommendations
                case '0':
                    recommended_meal = RecommendationService.get_meal_recommendations(user, time)
                    print("Recommended Meal:")
                    recommended_meal.print_meal()
                    recommended_meal.log_meal_into_db(user.id, 'recommended')
                # Log a meal
                case '1':
                    meal = Meal({}, time)
                    while True:
                        food_name = input("Enter food name to add (or 'done' to finish): ")
                        if food_name.lower() == 'done':
                            break
                        if Meal.get_food_nutrition_by_name(food_name) is None:
                            print(f"Food item '{food_name}' not found in database. Please try again.")
                            continue
                        quantity = float(input(f"Enter quantity of {food_name} in grams: "))
                        meal.food_items_quantity[food_name] = quantity
                    meal.log_meal_into_db(user.id, 'actual')
                    food_name_list = pd.Series(list(meal.food_items_quantity.keys())).unique()
                    # update preference model with new meal data
                    preference_model = PreferenceAlgo.train_or_update_model()
                    # update preference prediction
                    for food in food_name_list:
                        preference_score = PreferenceAlgo.predict_preference(
                            preference_model, user.id, food, 0, meal.food_items_quantity[food], food_name_list)
                        print(f'Updated preference probability for {food}: {preference_score}')
                # Add food items to database
                case '2':
                    food_name = input("Enter food name: ")
                    food_type = input("Enter food type (e.g., fruit, vegetable, meat): ")
                    calories = float(input("Enter calories per 100g: "))
                    protein = float(input("Enter protein per 100g: "))
                    carbohydrates = float(input("Enter carbohydrates per 100g: "))
                    fats = float(input("Enter fats per 100g: "))
                    Meal.add_food_item(food_name, food_type, calories, protein, carbohydrates, fats)
                # Update weight
                case '3':
                    new_weight = float(input("Enter your new weight in kg: "))
                    user.update_weight(new_weight, time)
                    # update activity level model with new weight data
                    X, y, activity_categories = ActivityLvAlgo.fetch_activity_data()
                    activity_model = ActivityLvAlgo.train_or_update_model(X, y)
                    # update activity level prediction
                    predicted_level = ActivityLvAlgo.predict_activity_level(activity_model, user, activity_categories)
                    print(f"Updated activity level: {predicted_level}")
                    # update weight gain/loss model with new weight data
                    factors = WeightGLAlgo.update_weight_gain_loss_factor(user)
                    print(f"Updated weight gain/loss factors: {factors}")
                # Update user info
                case '4':
                    new_height = float(input("Enter your new height in cm: "))
                    new_weight = float(input("Enter your new weight in kg: "))
                    new_sex = input("Enter your new sex (M/F): ").upper()
                    new_age = int(input("Enter your new age in years: "))
                    user.update_personal_info_to_db(new_height, new_weight, new_sex, new_age)
                    print("User info updated.")
                # Update user goal
                case '5':
                    new_estimated_days = int(input("Enter your new estimated days to reach target weight in days: "))
                    new_target_weight = float(input("Enter your new target weight in kg: "))
                    user.update_goal_to_db(new_estimated_days, new_target_weight)
                    print("User goal updated.")
                # Logout
                case '6':
                    AuthService.user_logout(user)
                    break
                # Delete account
                case '7':
                    AuthService.delete_user_from_db(user)
                    break
                # Default case for invalid command
                case _:
                    print("Invalid command. Please try again.")


if __name__ == "__main__":
    main()