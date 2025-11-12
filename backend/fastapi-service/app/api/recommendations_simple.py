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
from openai import OpenAI

logger = logging.getLogger(__name__)

router = APIRouter()

# OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

# Translation cache (English -> Korean)
translation_cache: Dict[str, str] = load_translation_cache()
logger.info(f"Loaded {len(translation_cache)} translations from cache")

# Create reverse cache (Korean -> English)
reverse_translation_cache: Dict[str, str] = {v: k for k, v in translation_cache.items()}

def save_translation_cache():
    """Save translation cache to JSON file"""
    try:
        with open(TRANSLATION_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(translation_cache, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(translation_cache)} translations to cache")
    except Exception as e:
        logger.error(f"Failed to save translation cache: {e}")

def translate_korean_to_english(korean_name: str) -> str:
    """Translate Korean meal name to English using OpenAI"""
    # Check cache first
    if korean_name in reverse_translation_cache:
        return reverse_translation_cache[korean_name]

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional translator. Translate Korean food dish names to English. Return ONLY the English translation, nothing else. Keep special characters and formatting (parentheses, etc)."
                },
                {
                    "role": "user",
                    "content": f"Translate this Korean dish name to English: {korean_name}"
                }
            ],
            temperature=0.3,
            max_tokens=100
        )

        english_name = response.choices[0].message.content.strip()
        logger.info(f"Translated '{korean_name}' to '{english_name}'")

        # Add to both caches
        translation_cache[english_name] = korean_name
        reverse_translation_cache[korean_name] = english_name

        # Save to file
        save_translation_cache()

        return english_name

    except Exception as e:
        logger.error(f"Error translating '{korean_name}': {e}")
        return korean_name  # Fallback to Korean name


def translate_recommendations(meals: List[dict]) -> List[dict]:
    """Translate only the recommended meals (not all meals in database)"""
    for meal in meals:
        # Only translate if name_en is still in Korean (not already translated)
        if meal["name_en"] == meal["name"]:  # name_en is same as Korean name
            korean_name = meal["name"]
            # Translate using OpenAI if not in cache
            english_name = translate_korean_to_english(korean_name)
            meal["name_en"] = english_name

    return meals

# Allergen mappings - map user-selected allergens to various forms
ALLERGEN_MAPPINGS = {
    'eggs': ['egg', 'eggs', '계란', '달걀', '난류', '에그'],
    'milk': ['milk', 'dairy', 'cheese', 'cream', 'butter', 'yogurt', 'whey', '우유', '유제품', '치즈', '크림', '버터', '요거트', '요구르트'],
    'buckwheat': ['buckwheat', 'soba', '메밀', '소바'],
    'peanuts': ['peanut', 'peanuts', '땅콩'],
    'soybeans': ['soy', 'soybean', 'tofu', 'miso', '대두', '콩', '두부', '된장', '간장'],
    'wheat': ['wheat', 'flour', 'bread', 'pasta', 'gluten', '밀', '밀가루', '빵', '면', '글루텐'],
    'mackerel': ['mackerel', 'saba', '고등어', '사바'],
    'crab': ['crab', '게'],
    'shrimp': ['shrimp', 'prawn', '새우'],
    'pork': ['pork', 'ham', 'bacon', '돼지', '돼지고기', '삼겹살', '베이컨', '햄'],
    'peach': ['peach', '복숭아'],
    'tomato': ['tomato', '토마토'],
    'sulfites': ['sulfite', 'sulfites', '아황산'],
    'walnuts': ['walnut', 'walnuts', '호두'],
    'chicken': ['chicken', 'poultry', '닭', '치킨', '닭고기'],
    'beef': ['beef', 'steak', '소고기', '쇠고기', '스테이크', '불고기'],
    'squid': ['squid', 'calamari', '오징어', '갈라마리'],
    'shellfish': ['shellfish', 'clam', 'mussel', 'oyster', 'scallop', '조개', '홍합', '굴', '가리비'],
    'pine_nuts': ['pine nut', 'pine nuts', '잣'],
    'crustaceans': ['crustacean', 'crustaceans', 'lobster', '갑각류', '랍스터'],
    'tree_nuts': ['almond', 'cashew', 'hazelnut', 'pecan', 'pistachio', 'nut', '견과류', '아몬드', '캐슈', '헤이즐넛'],
    'dairy': ['milk', 'dairy', 'cheese', 'cream', 'butter', 'yogurt', '유제품', '우유', '치즈']
}

def check_allergen_match(allergen_key: str, food_name: str, allergen_field: str) -> bool:
    """
    Check if a food contains a specific allergen
    Uses allergen mappings to check both the allergen field and food name
    """
    # Get all possible forms of this allergen
    allergen_variations = ALLERGEN_MAPPINGS.get(allergen_key, [allergen_key])

    # Convert to lowercase for comparison
    food_name_lower = food_name.lower()
    allergen_field_lower = allergen_field.lower()

    # Check each variation
    for variation in allergen_variations:
        variation_lower = variation.lower()
        # Check in allergen field
        if variation_lower in allergen_field_lower:
            return True
        # Check in food name (Korean food detection)
        if variation_lower in food_name_lower:
            return True

    return False


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

                # Get English translation from cache only (don't translate during load)
                english_name = reverse_translation_cache.get(korean_name, korean_name)

                meal = {
                    "name": korean_name,
                    "name_en": english_name,  # Use English translation
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

        # Calculate macro targets based on health goal (BEFORE filtering)
        if request.health_goal == "근육증가":
            # High protein for muscle gain
            target_protein_g = request.weight_kg * 2.2  # 2.2g per kg
            target_fat_g = request.weight_kg * 1.0  # 1g per kg
            protein_calories = target_protein_g * 4
            fat_calories = target_fat_g * 9
            carbs_calories = target_calories - protein_calories - fat_calories
            target_carbs_g = carbs_calories / 4
        elif request.health_goal == "체중감량":
            # Higher protein for weight loss
            target_protein_g = request.weight_kg * 2.0  # 2g per kg
            target_fat_g = request.weight_kg * 0.8  # 0.8g per kg
            protein_calories = target_protein_g * 4
            fat_calories = target_fat_g * 9
            carbs_calories = target_calories - protein_calories - fat_calories
            target_carbs_g = carbs_calories / 4
        else:  # 체중유지
            # Balanced macros
            target_protein_g = request.weight_kg * 1.6  # 1.6g per kg
            target_fat_g = request.weight_kg * 0.9  # 0.9g per kg
            protein_calories = target_protein_g * 4
            fat_calories = target_fat_g * 9
            carbs_calories = target_calories - protein_calories - fat_calories
            target_carbs_g = carbs_calories / 4

        # Calculate target macro ratios
        total_target_macros = target_protein_g + target_carbs_g + target_fat_g
        target_protein_ratio = target_protein_g / total_target_macros if total_target_macros > 0 else 0.33
        target_carbs_ratio = target_carbs_g / total_target_macros if total_target_macros > 0 else 0.53
        target_fat_ratio = target_fat_g / total_target_macros if total_target_macros > 0 else 0.14

        logger.info(f"Target macro ratios - Protein: {target_protein_ratio:.1%}, Carbs: {target_carbs_ratio:.1%}, Fat: {target_fat_ratio:.1%}")

        # Filter meals
        filtered_meals = []
        allergen_filtered_count = 0
        for meal in all_meals:
            # Skip if allergens match (enhanced check with mappings)
            skip = False
            for allergy in request.allergies:
                if check_allergen_match(allergy, meal["name"], meal.get("allergens", "")):
                    skip = True
                    allergen_filtered_count += 1
                    break

            if skip:
                continue

            # Skip very high calorie meals (more than 40% of daily target)
            if meal["calories"] > target_calories * 0.4:
                continue

            # Skip meals with extremely unbalanced macros
            total_macros = meal["protein_g"] + meal["carbs_g"] + meal["fat_g"]
            if total_macros > 0:
                protein_ratio = meal["protein_g"] / total_macros
                carbs_ratio = meal["carbs_g"] / total_macros
                fat_ratio = meal["fat_g"] / total_macros

                # Skip if any single macro is more than 95% (e.g., pure oil/sugar)
                if protein_ratio > 0.95 or carbs_ratio > 0.95 or fat_ratio > 0.95:
                    continue

                # Skip if protein is less than 5% (except for very low calorie meals)
                if meal["calories"] > 100 and protein_ratio < 0.05:
                    continue

            # Calculate simple score based on calorie appropriateness
            calorie_per_meal_target = target_calories / 3  # Assuming 3 meals per day
            calorie_diff = abs(meal["calories"] - calorie_per_meal_target)
            calorie_score = max(0, 100 - (calorie_diff / calorie_per_meal_target * 100))

            # Calculate macro similarity score based on user's target ratios (0-100)
            macro_similarity_score = 100
            if meal["calories"] > 100 and total_macros > 0:
                # Calculate absolute differences from target ratios
                protein_diff = abs(protein_ratio - target_protein_ratio)
                carbs_diff = abs(carbs_ratio - target_carbs_ratio)
                fat_diff = abs(fat_ratio - target_fat_ratio)

                # Calculate similarity score (lower difference = higher score)
                # Each macro can contribute up to ~33 points of penalty
                protein_penalty = protein_diff * 150  # 0-150 penalty range
                carbs_penalty = carbs_diff * 100      # 0-100 penalty range
                fat_penalty = fat_diff * 150          # 0-150 penalty range

                total_penalty = protein_penalty + carbs_penalty + fat_penalty
                macro_similarity_score = max(0, 100 - total_penalty)

            # Combined score (50% calorie, 50% macro similarity to user's target)
            score = (calorie_score * 0.5) + (macro_similarity_score * 0.5)

            # Boost score for high protein if muscle gain
            if request.health_goal == "근육증가" and meal["protein_g"] > 20:
                score += 5

            # Boost score for lower calorie if weight loss
            if request.health_goal == "체중감량" and meal["calories"] < calorie_per_meal_target:
                score += 3

            meal["score"] = min(100, score)
            filtered_meals.append(meal)

        # Sort by score and get top N
        filtered_meals.sort(key=lambda x: x["score"], reverse=True)
        recommendations = filtered_meals[:request.num_recommendations]

        # Add some randomness to avoid always showing the same meals
        if len(recommendations) > request.num_recommendations:
            recommendations = random.sample(filtered_meals[:50], min(request.num_recommendations, 50))

        # Translate only the recommended meals (not all 5723 meals!)
        recommendations = translate_recommendations(recommendations)

        # Log allergen filtering stats
        if request.allergies:
            logger.info(f"Allergen filtering: {allergen_filtered_count} meals filtered out for allergies: {request.allergies}")
            logger.info(f"Remaining meals after allergen filter: {len(filtered_meals)}")

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
                    "protein_g": round(target_protein_g, 1),
                    "carbs_g": round(target_carbs_g, 1),
                    "fat_g": round(target_fat_g, 1)
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
