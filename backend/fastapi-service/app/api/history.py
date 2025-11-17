"""
History API endpoints for user's meal recommendations and OCR product registrations
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging

from app.db.database import get_db
from app.models.user import User
from app.models.food_product import FoodProduct
from app.models.recommendation_history import RecommendationHistory
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class AddRecommendationRequest(BaseModel):
    meal_code: str
    meal_name_ko: str
    meal_name_en: Optional[str] = None
    calories: Optional[int] = None
    carbohydrates: Optional[int] = None
    protein: Optional[int] = None
    fat: Optional[int] = None
    sodium: Optional[int] = None
    recommendation_context: Optional[Dict[str, Any]] = None


@router.post("/recommendations/add")
async def add_recommendation_to_history(
    request: AddRecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a selected meal recommendation to user's history

    Args:
        request: Meal information
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status and created history entry
    """
    try:
        new_history = RecommendationHistory(
            user_id=current_user.id,
            meal_code=request.meal_code,
            meal_name_ko=request.meal_name_ko,
            meal_name_en=request.meal_name_en,
            calories=request.calories,
            carbohydrates=request.carbohydrates,
            protein=request.protein,
            fat=request.fat,
            sodium=request.sodium,
            recommendation_context=request.recommendation_context
        )

        db.add(new_history)
        db.commit()
        db.refresh(new_history)

        logger.info(f"Added recommendation to history: {new_history.meal_name_ko} for user {current_user.id}")

        return {
            "success": True,
            "message": "Recommendation added to history",
            "history_id": new_history.id
        }

    except Exception as e:
        logger.error(f"Error adding recommendation to history: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add recommendation to history: {str(e)}"
        )


@router.get("/recommendations")
async def get_recommendation_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's recommendation history

    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        current_user: Authenticated user
        db: Database session

    Returns:
        List of recommendation history
    """
    try:
        history = db.query(RecommendationHistory)\
            .filter(RecommendationHistory.user_id == current_user.id)\
            .order_by(desc(RecommendationHistory.selected_at))\
            .offset(skip)\
            .limit(limit)\
            .all()

        return {
            "success": True,
            "count": len(history),
            "history": [
                {
                    "id": h.id,
                    "meal_code": h.meal_code,
                    "meal_name_ko": h.meal_name_ko,
                    "meal_name_en": h.meal_name_en,
                    "nutrition_info": {
                        "calories": h.calories,
                        "carbohydrates": h.carbohydrates,
                        "protein": h.protein,
                        "fat": h.fat,
                        "sodium": h.sodium
                    },
                    "recommendation_context": h.recommendation_context,
                    "selected_at": h.selected_at.isoformat() if h.selected_at else None
                }
                for h in history
            ]
        }

    except Exception as e:
        logger.error(f"Error getting recommendation history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommendation history: {str(e)}"
        )


@router.get("/products")
async def get_product_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's OCR product registration history

    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        current_user: Authenticated user
        db: Database session

    Returns:
        List of registered products
    """
    try:
        products = db.query(FoodProduct)\
            .filter(FoodProduct.user_id == current_user.id)\
            .order_by(desc(FoodProduct.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()

        return {
            "success": True,
            "count": len(products),
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "allergens": p.allergens,
                    "nutrition_info": {
                        "calories": p.calories,
                        "carbohydrates": p.carbohydrates,
                        "protein": p.protein,
                        "fat": p.fat,
                        "sodium": p.sodium,
                        "sugar": p.sugar
                    },
                    "created_at": p.created_at.isoformat() if p.created_at else None
                }
                for p in products
            ]
        }

    except Exception as e:
        logger.error(f"Error getting product history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get product history: {str(e)}"
        )


@router.get("/all")
async def get_all_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all history (recommendations and products) for the user

    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        current_user: Authenticated user
        db: Database session

    Returns:
        Combined list of recommendations and products
    """
    try:
        # Get recommendations
        recommendations = db.query(RecommendationHistory)\
            .filter(RecommendationHistory.user_id == current_user.id)\
            .order_by(desc(RecommendationHistory.selected_at))\
            .all()

        # Get products
        products = db.query(FoodProduct)\
            .filter(FoodProduct.user_id == current_user.id)\
            .order_by(desc(FoodProduct.created_at))\
            .all()

        return {
            "success": True,
            "recommendations": {
                "count": len(recommendations),
                "items": [
                    {
                        "id": h.id,
                        "meal_code": h.meal_code,
                        "meal_name_ko": h.meal_name_ko,
                        "meal_name_en": h.meal_name_en,
                        "nutrition_info": {
                            "calories": h.calories,
                            "carbohydrates": h.carbohydrates,
                            "protein": h.protein,
                            "fat": h.fat,
                            "sodium": h.sodium
                        },
                        "recommendation_context": h.recommendation_context,
                        "selected_at": h.selected_at.isoformat() if h.selected_at else None
                    }
                    for h in recommendations[:limit]
                ]
            },
            "products": {
                "count": len(products),
                "items": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "allergens": p.allergens,
                        "nutrition_info": {
                            "calories": p.calories,
                            "carbohydrates": p.carbohydrates,
                            "protein": p.protein,
                            "fat": p.fat,
                            "sodium": p.sodium,
                            "sugar": p.sugar
                        },
                        "created_at": p.created_at.isoformat() if p.created_at else None
                    }
                    for p in products[:limit]
                ]
            }
        }

    except Exception as e:
        logger.error(f"Error getting all history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get all history: {str(e)}"
        )
