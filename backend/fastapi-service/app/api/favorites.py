"""
Favorites API endpoints for user's favorite meals
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
import logging

from app.db.database import get_db
from app.models.user import User
from app.models.favorite import Favorite
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class AddFavoriteRequest(BaseModel):
    meal_code: str
    meal_name_ko: str
    meal_name_en: Optional[str] = None
    calories: Optional[int] = None
    carbohydrates: Optional[int] = None
    protein: Optional[int] = None
    fat: Optional[int] = None
    sodium: Optional[int] = None


@router.post("/add")
async def add_to_favorites(
    request: AddFavoriteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a meal to user's favorites

    Args:
        request: Meal information
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status and created favorite entry
    """
    try:
        # Check if already favorited
        existing = db.query(Favorite).filter(
            Favorite.user_id == current_user.id,
            Favorite.meal_code == request.meal_code
        ).first()

        if existing:
            return {
                "success": True,
                "message": "Meal already in favorites",
                "favorite_id": existing.id,
                "already_exists": True
            }

        new_favorite = Favorite(
            user_id=current_user.id,
            meal_code=request.meal_code,
            meal_name_ko=request.meal_name_ko,
            meal_name_en=request.meal_name_en,
            calories=request.calories,
            carbohydrates=request.carbohydrates,
            protein=request.protein,
            fat=request.fat,
            sodium=request.sodium
        )

        db.add(new_favorite)
        db.commit()
        db.refresh(new_favorite)

        logger.info(f"Added to favorites: {new_favorite.meal_name_ko} for user {current_user.id}")

        return {
            "success": True,
            "message": "Added to favorites",
            "favorite_id": new_favorite.id,
            "already_exists": False
        }

    except IntegrityError:
        db.rollback()
        return {
            "success": True,
            "message": "Meal already in favorites",
            "already_exists": True
        }
    except Exception as e:
        logger.error(f"Error adding to favorites: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add to favorites: {str(e)}"
        )


@router.delete("/remove/{meal_code}")
async def remove_from_favorites(
    meal_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a meal from user's favorites

    Args:
        meal_code: Code of the meal to remove
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status
    """
    try:
        favorite = db.query(Favorite).filter(
            Favorite.user_id == current_user.id,
            Favorite.meal_code == meal_code
        ).first()

        if not favorite:
            raise HTTPException(
                status_code=404,
                detail="Favorite not found"
            )

        db.delete(favorite)
        db.commit()

        logger.info(f"Removed from favorites: {meal_code} for user {current_user.id}")

        return {
            "success": True,
            "message": "Removed from favorites"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from favorites: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove from favorites: {str(e)}"
        )


@router.get("/list")
async def get_favorites(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's favorite meals

    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        current_user: Authenticated user
        db: Database session

    Returns:
        List of favorite meals
    """
    try:
        favorites = db.query(Favorite)\
            .filter(Favorite.user_id == current_user.id)\
            .order_by(desc(Favorite.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()

        return {
            "success": True,
            "count": len(favorites),
            "favorites": [
                {
                    "id": f.id,
                    "meal_code": f.meal_code,
                    "meal_name_ko": f.meal_name_ko,
                    "meal_name_en": f.meal_name_en,
                    "nutrition_info": {
                        "calories": f.calories,
                        "carbohydrates": f.carbohydrates,
                        "protein": f.protein,
                        "fat": f.fat,
                        "sodium": f.sodium
                    },
                    "created_at": f.created_at.isoformat() if f.created_at else None
                }
                for f in favorites
            ]
        }

    except Exception as e:
        logger.error(f"Error getting favorites: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get favorites: {str(e)}"
        )


@router.get("/check/{meal_code}")
async def check_favorite(
    meal_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if a meal is favorited by the user

    Args:
        meal_code: Code of the meal to check
        current_user: Authenticated user
        db: Database session

    Returns:
        Whether the meal is favorited
    """
    try:
        favorite = db.query(Favorite).filter(
            Favorite.user_id == current_user.id,
            Favorite.meal_code == meal_code
        ).first()

        return {
            "success": True,
            "is_favorited": favorite is not None,
            "favorite_id": favorite.id if favorite else None
        }

    except Exception as e:
        logger.error(f"Error checking favorite: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check favorite: {str(e)}"
        )
