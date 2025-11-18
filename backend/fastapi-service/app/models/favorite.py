"""
Favorite model for user's favorite meals
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Favorite(Base):
    """Track meals that users marked as favorites"""

    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Meal information (stored as snapshot)
    meal_code = Column(String, nullable=False)
    meal_name_ko = Column(String, nullable=False)
    meal_name_en = Column(String, nullable=True)

    # Nutrition information
    calories = Column(Integer, nullable=True)
    carbohydrates = Column(Integer, nullable=True)
    protein = Column(Integer, nullable=True)
    fat = Column(Integer, nullable=True)
    sodium = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to User
    user = relationship("User", back_populates="favorites")

    # Ensure a user can only favorite the same meal once
    __table_args__ = (
        UniqueConstraint('user_id', 'meal_code', name='unique_user_meal_favorite'),
    )

    def __repr__(self):
        return f"<Favorite(id={self.id}, user_id={self.user_id}, meal='{self.meal_name_ko}')>"
