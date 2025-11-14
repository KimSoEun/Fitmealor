"""
Food Product model for user-scanned products
"""

from sqlalchemy import Column, Integer, String, Float, JSON, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class FoodProduct(Base):
    """User-scanned food products from OCR"""

    __tablename__ = "food_products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    # Nutrition information
    calories = Column(Float, nullable=True)
    carbohydrates = Column(Float, nullable=True)
    protein = Column(Float, nullable=True)
    fat = Column(Float, nullable=True)
    sodium = Column(Float, nullable=True)
    sugar = Column(Float, nullable=True)

    # Allergens stored as JSON array
    allergens = Column(JSON, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<FoodProduct(id={self.id}, name='{self.name}')>"
