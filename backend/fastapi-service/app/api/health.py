"""Health API router"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/profile")
async def get_health_profile():
    return {"message": "Health profile endpoint"}
