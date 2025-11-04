"""Meals API router"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_meals():
    return {"message": "Meals endpoint"}

@router.get("/{meal_id}")
async def get_meal(meal_id: str):
    return {"meal_id": meal_id}
