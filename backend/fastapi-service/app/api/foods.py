"""
Foods API endpoints for product registration
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import logging

from app.db.database import get_db
from app.models.food_product import FoodProduct
from app.models.user import User
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class NutritionInfoRequest(BaseModel):
    calories: Optional[float] = None
    carbohydrates: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    sodium: Optional[float] = None
    sugar: Optional[float] = None


class RegisterProductRequest(BaseModel):
    name: Optional[str] = None
    allergens: Optional[List[str]] = []
    nutrition_info: Optional[NutritionInfoRequest] = None


@router.post("/register")
async def register_product(
    request: RegisterProductRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register a new food product from OCR scanning

    Args:
        request: Product information including name, allergens, and nutrition
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status and created product ID
    """
    try:
        # Validate that at least product name is provided
        if not request.name or request.name.strip() == "":
            raise HTTPException(
                status_code=400,
                detail="Product name is required"
            )

        # Create new food product with user_id
        new_product = FoodProduct(
            user_id=current_user.id,
            name=request.name.strip(),
            allergens=request.allergens or [],
            calories=request.nutrition_info.calories if request.nutrition_info else None,
            carbohydrates=request.nutrition_info.carbohydrates if request.nutrition_info else None,
            protein=request.nutrition_info.protein if request.nutrition_info else None,
            fat=request.nutrition_info.fat if request.nutrition_info else None,
            sodium=request.nutrition_info.sodium if request.nutrition_info else None,
            sugar=request.nutrition_info.sugar if request.nutrition_info else None,
        )

        # Save to database
        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        logger.info(f"Registered new product: {new_product.name} (ID: {new_product.id}) for user {current_user.id}")

        return {
            "success": True,
            "product_id": new_product.id,
            "message": "Product registered successfully",
            "product": {
                "id": new_product.id,
                "name": new_product.name,
                "allergens": new_product.allergens,
                "nutrition_info": {
                    "calories": new_product.calories,
                    "carbohydrates": new_product.carbohydrates,
                    "protein": new_product.protein,
                    "fat": new_product.fat,
                    "sodium": new_product.sodium,
                    "sugar": new_product.sugar
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering product: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register product: {str(e)}"
        )


@router.get("/products")
async def list_products(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of registered food products for the current user

    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        current_user: Authenticated user
        db: Database session

    Returns:
        List of food products for the current user
    """
    try:
        products = db.query(FoodProduct)\
            .filter(FoodProduct.user_id == current_user.id)\
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
        logger.error(f"Error listing products: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list products: {str(e)}"
        )


@router.get("/products/{product_id}")
async def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific food product by ID (only for the current user)

    Args:
        product_id: Product ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Product details
    """
    try:
        product = db.query(FoodProduct)\
            .filter(FoodProduct.id == product_id, FoodProduct.user_id == current_user.id)\
            .first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product with ID {product_id} not found"
            )

        return {
            "success": True,
            "product": {
                "id": product.id,
                "name": product.name,
                "allergens": product.allergens,
                "nutrition_info": {
                    "calories": product.calories,
                    "carbohydrates": product.carbohydrates,
                    "protein": product.protein,
                    "fat": product.fat,
                    "sodium": product.sodium,
                    "sugar": product.sugar
                },
                "created_at": product.created_at.isoformat() if product.created_at else None,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get product: {str(e)}"
        )
