# AI Nutritionist Application

## Overview
The AI Nutritionist Application is designed to help users manage their nutrition and achieve their health goals. By inputting personal data such as height, weight, sex, age, and target weight, users can track their daily meals and current weight. The application utilizes a decision tree to provide meal ratings and recommendations based on nutritional data.

## Features
- User input for personal health metrics and daily meals.
- Decision tree logic for meal rating and recommendations.
- Database integration for food nutrition, recommended intake, and user history.
- Tracking of daily meals and weight changes over time.

## Project Structure
```
ai-nutritionist-app
├── src
│   ├── main.py                # Entry point of the application
│   ├── decision_tree.py       # Decision tree logic for meal recommendations
│   ├── database
│   │   ├── food_nutrition.sql # Nutritional information for various foods
│   │   ├── recommended_intake.sql # Daily recommended nutrition intake
│   │   └── from utils.nutrition_utils import NutritionUtilsory.sql    # User consumption and weight history
│   ├── models
│   │   ├── user.py            # User class definition
│   │   ├── meal.py            # Meal class definition
│   │   └── recommendation.py   # Recommendation class definition
│   ├── utils
│   │   └── nutrition_utils.py  # Utility functions for nutrition calculations
│   └── services
│       ├── meal_tracker.py     # Services for tracking meals
│       └── recommendation_service.py # Services for meal recommendations
├── requirements.txt            # Project dependencies
└── README.md                   # Project documentation
```

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd ai-nutritionist-app
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
1. Run the application:
   ```
   python src/main.py
   ```
2. Follow the prompts to enter your personal information and track your meals.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License.