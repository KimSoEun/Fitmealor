"""
User database model for authentication
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    target_weight_kg = Column(Float, nullable=True)
    activity_level = Column(String, nullable=True)
    health_goal = Column(String, nullable=True)
    allergens = Column(JSON, nullable=True)  # List of allergens (22 types)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    food_products = relationship("FoodProduct", back_populates="user")
    recommendation_history = relationship("RecommendationHistory", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")
