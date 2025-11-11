"""
Simple Meal Recommendation API endpoints (without torch dependency)
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel
import logging
import csv
import os
import random
import json

logger = logging.getLogger(__name__)

router = APIRouter()

# Translation cache file path
TRANSLATION_CACHE_FILE = "/Users/goorm/Fitmealor/backend/data/meal_name_translations.json"

# Load translation cache from file
def load_translation_cache() -> Dict[str, str]:
    """Load translation cache from JSON file"""
    if os.path.exists(TRANSLATION_CACHE_FILE):
        try:
            with open(TRANSLATION_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load translation cache: {e}")
            return {}
    return {}

# Translation cache
translation_cache: Dict[str, str] = load_translation_cache()
logger.info(f"Loaded {len(translation_cache)} translations from cache")


class RecommendationRequest(BaseModel):
    user_id: str
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    target_weight_kg: float
    activity_level: str
    health_goal: str
    allergies: List[str] = []
    dietary_restrictions: List[str] = []
    num_recommendations: int = 15


class MealResponse(BaseModel):
    name: str
    name_en: str
    name_kr: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    category: str
    score: float


def load_meals_from_csv():
    """Load meals from both Korean food database (xlsx) and CSV"""
    import pandas as pd

    meals = []

    # Load from xlsx (Korean food database)
    xlsx_path = "/Users/goorm/Fitmealor/backend/data/20250408_음식DB.xlsx"
    try:
        df = pd.read_excel(xlsx_path)

        for _, row in df.iterrows():
            try:
                korean_name = row["식품명"]

                # Skip if essential data is missing (name, calories, or any major macronutrient)
                if (pd.isna(korean_name) or
                    pd.isna(row["에너지(kcal)"]) or
                    pd.isna(row["단백질(g)"]) or
                    pd.isna(row["탄수화물(g)"]) or
                    pd.isna(row["지방(g)"])):
                    continue

                meal = {
                    "name": korean_name,
                    "name_en": korean_name,  # Korean meals don't have English translation
                    "name_kr": korean_name,
                    "calories": float(row["에너지(kcal)"]),
                    "protein_g": float(row["단백질(g)"]),
                    "carbs_g": float(row["탄수화물(g)"]),
                    "fat_g": float(row["지방(g)"]),
                    "category": row.get("식품대분류명", "기타"),
                    "meal_type": "",
                    "allergens": "",
                }
                meals.append(meal)
            except (ValueError, KeyError) as e:
                logger.error(f"Error processing xlsx row: {e}")
                continue

        logger.info(f"Loaded {len(meals)} meals from Korean xlsx database")

    except FileNotFoundError:
        logger.error(f"xlsx file not found: {xlsx_path}")
    except Exception as e:
        logger.error(f"Error loading xlsx: {e}")

    # Load from CSV (English food database)
    csv_path = "/Users/goorm/Fitmealor/backend/data/fitmealor_nutrition_filled.csv"
    csv_meal_count = 0
    try:
        import csv as csv_module

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv_module.DictReader(f)
            for row in reader:
                try:
                    english_name = row["Dish Name"]

                    # Skip if essential data is missing
                    if not english_name or not row.get("Calories (kcal)"):
                        continue

                    # Parse nutrition values
                    try:
                        calories = float(row["Calories (kcal)"])
                        protein = float(row.get("Protein (g)", 0))
                        carbs = float(row.get("Carbohydrates (g)", 0))
                        fat = float(row.get("Fat (g)", 0))
                    except (ValueError, TypeError):
                        continue

                    # Skip meals with missing macro data (all zeros or impossible values)
                    if calories > 0 and (protein + carbs + fat == 0):
                        continue

                    # Skip meals with unrealistic macro ratios (e.g., 750g fat in 800 kcal meal)
                    # Total calories from macros should be roughly equal to stated calories
                    calculated_calories = (protein * 4) + (carbs * 4) + (fat * 9)
                    if calories > 0 and calculated_calories > 0:
                        ratio = calculated_calories / calories
                        if ratio < 0.5 or ratio > 2.0:  # Allow 50-200% range
                            continue

                    # Get Korean translation from cache if available
                    korean_name = translation_cache.get(english_name, english_name)

                    meal = {
                        "name": english_name,
                        "name_en": english_name,
                        "name_kr": korean_name,
                        "calories": calories,
                        "protein_g": protein,
                        "carbs_g": carbs,
                        "fat_g": fat,
                        "category": row.get("Cuisine", "기타"),
                        "meal_type": row.get("Meal Type", ""),
                        "allergens": row.get("Allergens", ""),
                    }
                    meals.append(meal)
                    csv_meal_count += 1
                except (ValueError, KeyError) as e:
                    logger.error(f"Error processing CSV row: {e}")
                    continue

        logger.info(f"Loaded {csv_meal_count} meals from CSV database")

    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_path}")
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")

    logger.info(f"Total meals loaded: {len(meals)} (xlsx + CSV)")
    return meals


@router.post("/recommend")
async def recommend_meals(request: RecommendationRequest):
    """
    Get personalized meal recommendations based on user profile
    """
    try:
        # Load meals from CSV
        all_meals = load_meals_from_csv()

        if not all_meals:
            raise HTTPException(status_code=500, detail="No meals available")

        # Calculate target calories based on health goal
        # Simple TDEE calculation (Harris-Benedict equation)
        if request.gender == "남성":
            bmr = 88.362 + (13.397 * request.weight_kg) + (4.799 * request.height_cm) - (5.677 * request.age)
        else:
            bmr = 447.593 + (9.247 * request.weight_kg) + (3.098 * request.height_cm) - (4.330 * request.age)

        # Activity level multiplier
        activity_multipliers = {
            "비활동적": 1.2,
            "가볍게 활동적": 1.375,
            "활동적": 1.55,
            "매우 활동적": 1.725
        }
        activity_multiplier = activity_multipliers.get(request.activity_level, 1.55)
        tdee = bmr * activity_multiplier

        # Adjust for health goal
        if request.health_goal == "체중감량":
            target_calories = tdee * 0.85  # 15% deficit
        elif request.health_goal == "근육증가":
            target_calories = tdee * 1.10  # 10% surplus
        else:  # 체중유지
            target_calories = tdee

        # Filter meals
        filtered_meals = []
        for meal in all_meals:
            # Skip if allergens match (simple check)
            skip = False
            for allergy in request.allergies:
                if allergy.lower() in meal.get("allergens", "").lower():
                    skip = True
                    break

            if skip:
                continue

            # Skip very high calorie meals (more than 40% of daily target)
            if meal["calories"] > target_calories * 0.4:
                continue

            # Calculate simple score based on calorie appropriateness
            calorie_per_meal_target = target_calories / 3  # Assuming 3 meals per day
            calorie_diff = abs(meal["calories"] - calorie_per_meal_target)
            score = max(0, 100 - (calorie_diff / calorie_per_meal_target * 100))

            # Boost score for high protein if muscle gain
            if request.health_goal == "근육증가" and meal["protein_g"] > 20:
                score += 10

            # Boost score for lower calorie if weight loss
            if request.health_goal == "체중감량" and meal["calories"] < calorie_per_meal_target:
                score += 5

            meal["score"] = min(100, score)
            filtered_meals.append(meal)

        # Sort by score and get top N
        filtered_meals.sort(key=lambda x: x["score"], reverse=True)
        recommendations = filtered_meals[:request.num_recommendations]

        # Add some randomness to avoid always showing the same meals
        if len(recommendations) > request.num_recommendations:
            recommendations = random.sample(filtered_meals[:50], min(request.num_recommendations, 50))

        # Calculate macro targets based on health goal
        if request.health_goal == "근육증가":
            # High protein for muscle gain
            protein_g = request.weight_kg * 2.2  # 2.2g per kg
            fat_g = request.weight_kg * 1.0  # 1g per kg
            protein_calories = protein_g * 4
            fat_calories = fat_g * 9
            carbs_calories = target_calories - protein_calories - fat_calories
            carbs_g = carbs_calories / 4
        elif request.health_goal == "체중감량":
            # Higher protein for weight loss
            protein_g = request.weight_kg * 2.0  # 2g per kg
            fat_g = request.weight_kg * 0.8  # 0.8g per kg
            protein_calories = protein_g * 4
            fat_calories = fat_g * 9
            carbs_calories = target_calories - protein_calories - fat_calories
            carbs_g = carbs_calories / 4
        else:  # 체중유지
            # Balanced macros
            protein_g = request.weight_kg * 1.6  # 1.6g per kg
            fat_g = request.weight_kg * 0.9  # 0.9g per kg
            protein_calories = protein_g * 4
            fat_calories = fat_g * 9
            carbs_calories = target_calories - protein_calories - fat_calories
            carbs_g = carbs_calories / 4

        return {
            "success": True,
            "user_id": request.user_id,
            "total_recommendations": len(recommendations),
            "target_calories": round(target_calories, 2),
            "bmr": round(bmr, 2),
            "tdee": round(tdee, 2),
            "tdee_info": {
                "bmr": round(bmr, 2),
                "tdee": round(tdee, 2),
                "adjusted_tdee": round(target_calories, 2),
                "macro_targets": {
                    "calories": round(target_calories, 2),
                    "protein_g": round(protein_g, 1),
                    "carbs_g": round(carbs_g, 1),
                    "fat_g": round(fat_g, 1)
                }
            },
            "recommendations": recommendations
        }

    except Exception as e:
        logger.error(f"Error generating recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_recommendation():
    """Test endpoint"""
    return {
        "message": "Simple Recommendation API is working",
        "endpoints": [
            "/api/v1/recommendations/recommend"
        ]
    }
