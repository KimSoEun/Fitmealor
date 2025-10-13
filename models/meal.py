"""
Fitmealor models/meal.py
- SQLAlchemy 2.0 declarative models for meals/ingredients/nutrients/tags
- Pydantic schemas for DTOs

Note
- This file defines ImageAsset minimally to satisfy FKs from Meal/Ingredient.
- If you already have media models elsewhere, remove or import accordingly.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
import uuid

from sqlalchemy import (
    String, Integer, Numeric, Boolean, DateTime, ForeignKey, UniqueConstraint,
    CheckConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

# --- SQLAlchemy Base ---------------------------------------------------------
class Base(DeclarativeBase):
    pass


# --- Media (minimal) ---------------------------------------------------------
class ImageAsset(Base):
    __tablename__ = "image_asset"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    url: Mapped[str] = mapped_column(String, nullable=False)
    alt_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# --- Core Meal Models --------------------------------------------------------
class Meal(Base):
    __tablename__ = "meal"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    image_asset_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("image_asset.id"))

    calories: Mapped[Optional[float]] = mapped_column(Numeric(7, 2))
    protein_g: Mapped[Optional[float]] = mapped_column(Numeric(7, 2))
    fat_g: Mapped[Optional[float]] = mapped_column(Numeric(7, 2))
    carb_g: Mapped[Optional[float]] = mapped_column(Numeric(7, 2))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    image: Mapped[Optional[ImageAsset]] = relationship()
    i18n: Mapped[List["MealI18n"]] = relationship(back_populates="meal", cascade="all, delete-orphan")
    ingredients: Mapped[List["MealIngredient"]] = relationship(back_populates="meal", cascade="all, delete-orphan")
    nutrients: Mapped[List["MealNutrient"]] = relationship(back_populates="meal", cascade="all, delete-orphan")
    tags: Mapped[List["MealTag"]] = relationship(back_populates="meal", cascade="all, delete-orphan")


class MealI18n(Base):
    __tablename__ = "meal_i18n"
    __table_args__ = (
        UniqueConstraint("meal_id", "lang", name="uq_meal_lang_once"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    meal_id: Mapped[str] = mapped_column(String(36), ForeignKey("meal.id", ondelete="CASCADE"))
    lang: Mapped[str] = mapped_column(String(8), nullable=False)  # en|ko|ja...
    name_local: Mapped[str] = mapped_column(String, nullable=False)
    desc_local: Mapped[Optional[str]] = mapped_column(String)

    meal: Mapped[Meal] = relationship(back_populates="i18n")


class Ingredient(Base):
    __tablename__ = "ingredient"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_name: Mapped[str] = mapped_column(String, nullable=False)
    image_asset_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("image_asset.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    image: Mapped[Optional[ImageAsset]] = relationship()
    allergens: Mapped[List["IngredientAllergen"]] = relationship(back_populates="ingredient", cascade="all, delete-orphan")


class MealIngredient(Base):
    __tablename__ = "meal_ingredient"

    meal_id: Mapped[str] = mapped_column(String(36), ForeignKey("meal.id", ondelete="CASCADE"), primary_key=True)
    ingredient_id: Mapped[str] = mapped_column(String(36), ForeignKey("ingredient.id", ondelete="CASCADE"), primary_key=True)
    quantity_g: Mapped[Optional[float]] = mapped_column(Numeric(7, 2))

    meal: Mapped[Meal] = relationship(back_populates="ingredients")
    ingredient: Mapped[Ingredient] = relationship()


class Allergen(Base):
    __tablename__ = "allergen"

    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    display_name: Mapped[Optional[str]] = mapped_column(String)
    severity_default: Mapped[int] = mapped_column(Integer, default=2)  # 1..3


class IngredientAllergen(Base):
    __tablename__ = "ingredient_allergen"

    ingredient_id: Mapped[str] = mapped_column(String(36), ForeignKey("ingredient.id", ondelete="CASCADE"), primary_key=True)
    allergen_code: Mapped[str] = mapped_column(String(40), ForeignKey("allergen.code", ondelete="CASCADE"), primary_key=True)
    trace_possible: Mapped[bool] = mapped_column(Boolean, default=False)

    ingredient: Mapped[Ingredient] = relationship(back_populates="allergens")
    allergen: Mapped[Allergen] = relationship()


class Nutrient(Base):
    __tablename__ = "nutrient"

    code: Mapped[str] = mapped_column(String(40), primary_key=True)  # energy, protein, fat, carb, fiber, sodium...
    unit: Mapped[str] = mapped_column(String(16), nullable=False)    # kcal, g, mg...
    display_name: Mapped[Optional[str]] = mapped_column(String)


class MealNutrient(Base):
    __tablename__ = "meal_nutrient"

    meal_id: Mapped[str] = mapped_column(String(36), ForeignKey("meal.id", ondelete="CASCADE"), primary_key=True)
    nutrient_code: Mapped[str] = mapped_column(String(40), ForeignKey("nutrient.code", ondelete="CASCADE"), primary_key=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 3))

    meal: Mapped[Meal] = relationship(back_populates="nutrients")
    nutrient: Mapped[Nutrient] = relationship()


class CuisineTag(Base):
    __tablename__ = "cuisine_tag"

    code: Mapped[str] = mapped_column(String(40), primary_key=True)  # korean, japanese, halal, gluten_free, spicy...
    display_name: Mapped[Optional[str]] = mapped_column(String)


class MealTag(Base):
    __tablename__ = "meal_tag"

    meal_id: Mapped[str] = mapped_column(String(36), ForeignKey("meal.id", ondelete="CASCADE"), primary_key=True)
    tag_code: Mapped[str] = mapped_column(String(40), ForeignKey("cuisine_tag.code", ondelete="CASCADE"), primary_key=True)

    meal: Mapped[Meal] = relationship(back_populates="tags")
    tag: Mapped[CuisineTag] = relationship()


# --- Pydantic Schemas --------------------------------------------------------
try:
    from pydantic import BaseModel, Field, ConfigDict
    P2 = True
except Exception:  # pragma: no cover
    from pydantic import BaseModel, Field  # type: ignore
    P2 = False


class MealCreate(BaseModel):
    canonical_name: str
    description: Optional[str] = None
    image_asset_id: Optional[str] = None
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    carb_g: Optional[float] = None
    tags: Optional[List[str]] = None  # convenience

    if P2:
        model_config = ConfigDict(from_attributes=True)


class MealRead(BaseModel):
    id: str
    canonical_name: str
    description: Optional[str]
    image_asset_id: Optional[str]
    calories: Optional[float]
    protein_g: Optional[float]
    fat_g: Optional[float]
    carb_g: Optional[float]
    is_active: bool

    if P2:
        model_config = ConfigDict(from_attributes=True)


class IngredientRead(BaseModel):
    id: str
    canonical_name: str

    if P2:
        model_config = ConfigDict(from_attributes=True)


class MealNutrientRead(BaseModel):
    meal_id: str
    nutrient_code: str
    amount: float

    if P2:
        model_config = ConfigDict(from_attributes=True)


class MealI18nIn(BaseModel):
    meal_id: str
    lang: str
    name_local: str
    desc_local: Optional[str] = None

    if P2:
        model_config = ConfigDict(from_attributes=True)

