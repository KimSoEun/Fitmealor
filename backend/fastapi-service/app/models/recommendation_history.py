"""
Recommendation History model for tracking user's meal selections
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class RecommendationHistory(Base):
    """Track meals that users selected from recommendations"""

    __tablename__ = "recommendation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Meal information
    meal_code = Column(String, nullable=False)  # Code from meals database
    meal_name_ko = Column(String, nullable=False)
    meal_name_en = Column(String, nullable=True)

    # Nutrition information (snapshot at the time of selection)
    calories = Column(Integer, nullable=True)
    carbohydrates = Column(Integer, nullable=True)
    protein = Column(Integer, nullable=True)
    fat = Column(Integer, nullable=True)
    sodium = Column(Integer, nullable=True)

    # Additional metadata
    recommendation_context = Column(JSON, nullable=True)  # Store why it was recommended

    # Timestamps
    selected_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to User
    user = relationship("User", back_populates="recommendation_history")

    def __repr__(self):
        return f"<RecommendationHistory(id={self.id}, user_id={self.user_id}, meal='{self.meal_name_ko}')>"
