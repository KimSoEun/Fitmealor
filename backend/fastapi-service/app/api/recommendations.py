"""
Meal Recommendation API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.models.recommendation_model import (
    nutrition_model,
    UserProfile,
    MealData
)

logger = logging.getLogger(__name__)

router = APIRouter()


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
    symptoms: Optional[List[str]] = None
    health_conditions: Optional[List[str]] = None
    num_recommendations: int = 10


class MealRequest(BaseModel):
    meal_id: str
    name: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float = 0
    ingredients: List[str] = []
    allergens: List[str] = []
    is_vegetarian: bool = False
    is_vegan: bool = False
    is_halal: bool = False


@router.post("/analyze")
async def analyze_health_status(request: RecommendationRequest):
    """
    Analyze user health status and nutritional needs
    """
    try:
        profile = UserProfile(
            user_id=request.user_id,
            age=request.age,
            gender=request.gender,
            height_cm=request.height_cm,
            weight_kg=request.weight_kg,
            target_weight_kg=request.target_weight_kg,
            activity_level=request.activity_level,
            health_goal=request.health_goal,
            allergies=request.allergies,
            dietary_restrictions=request.dietary_restrictions,
            symptoms=request.symptoms,
            health_conditions=request.health_conditions
        )
        
        analysis = await nutrition_model.analyze_health_status(profile)
        
        return {
            "success": True,
            "user_id": request.user_id,
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"Error analyzing health status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend")
async def recommend_meals(
    request: RecommendationRequest,
    meals: List[MealRequest]
):
    """
    Get personalized meal recommendations
    
    Process:
    1. Analyze user health status and symptoms
    2. Infer deficient nutrients using nutrition expert prompt
    3. Search foods containing required nutrients
    4. Apply personalization filtering
    """
    try:
        # Convert request to UserProfile
        profile = UserProfile(
            user_id=request.user_id,
            age=request.age,
            gender=request.gender,
            height_cm=request.height_cm,
            weight_kg=request.weight_kg,
            target_weight_kg=request.target_weight_kg,
            activity_level=request.activity_level,
            health_goal=request.health_goal,
            allergies=request.allergies,
            dietary_restrictions=request.dietary_restrictions,
            symptoms=request.symptoms,
            health_conditions=request.health_conditions
        )
        
        # Convert meals to MealData
        meal_data = [
            MealData(
                meal_id=meal.meal_id,
                name=meal.name,
                calories=meal.calories,
                protein_g=meal.protein_g,
                carbs_g=meal.carbs_g,
                fat_g=meal.fat_g,
                fiber_g=meal.fiber_g,
                ingredients=meal.ingredients,
                allergens=meal.allergens,
                is_vegetarian=meal.is_vegetarian,
                is_vegan=meal.is_vegan,
                is_halal=meal.is_halal
            )
            for meal in meals
        ]
        
        # Get recommendations
        recommendations = await nutrition_model.recommend_meals(
            profile,
            meal_data,
            num_recommendations=request.num_recommendations
        )
        
        return {
            "success": True,
            "user_id": request.user_id,
            "total_recommendations": len(recommendations),
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_recommendation():
    """Test endpoint with sample data"""
    return {
        "message": "Recommendation API is working",
        "endpoints": [
            "/api/v1/recommendations/analyze",
            "/api/v1/recommendations/recommend"
        ]
    }
