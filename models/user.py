"""
Fitmealor models/user.py
- SQLAlchemy 2.0 declarative models
- Pydantic schemas for request/response DTOs

Notes
- If you already have a shared Base in models/base.py, replace the local Base with `from .base import Base`.
- UUIDs are stored as strings for cross‑DB portability. If you use PostgreSQL, you can switch to UUID type.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional
import uuid

from sqlalchemy import (
    String, Date, DateTime, ForeignKey, CheckConstraint, UniqueConstraint,
    text, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# --- SQLAlchemy Base ---------------------------------------------------------
class Base(DeclarativeBase):
    pass


# --- SQLAlchemy Models -------------------------------------------------------
class UserAccount(Base):
    __tablename__ = "user_account"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    auth_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="local")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # active|blocked|deleted
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False)
    preferences: Mapped[List["UserPreference"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    measures: Mapped[List["UserHealthMeasure"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profile"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_account.id", ondelete="CASCADE"), index=True)

    name: Mapped[Optional[str]] = mapped_column(String(120))
    gender: Mapped[Optional[str]] = mapped_column(String(20))  # female|male|other|unspecified
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    height_cm: Mapped[Optional[float]] = mapped_column()
    weight_kg: Mapped[Optional[float]] = mapped_column()
    country: Mapped[Optional[str]] = mapped_column(String(80))
    locale: Mapped[str] = mapped_column(String(10), default="en")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[UserAccount] = relationship(back_populates="profile")


class UserHealthMeasure(Base):
    __tablename__ = "user_health_measure"
    __table_args__ = (
        UniqueConstraint("user_id", "measure_date", name="uq_user_measure_once_per_day"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_account.id", ondelete="CASCADE"), index=True)

    measure_date: Mapped[date] = mapped_column(Date, nullable=False)
    weight_kg: Mapped[Optional[float]] = mapped_column()
    bmi: Mapped[Optional[float]] = mapped_column()
    bmr: Mapped[Optional[float]] = mapped_column()
    activity_level: Mapped[Optional[str]] = mapped_column(String(20))  # sedentary|light|moderate|active|very_active

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[UserAccount] = relationship(back_populates="measures")


class UserPreference(Base):
    __tablename__ = "user_preference"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_account.id", ondelete="CASCADE"), index=True)

    goal_type: Mapped[Optional[str]] = mapped_column(String(30))  # weight_loss|muscle_gain|balance|keto|low_carb|custom
    diet_type: Mapped[Optional[str]] = mapped_column(String(30))  # FK to diet_type.code (logical FK)
    allergy_codes: Mapped[Optional[str]] = mapped_column(String)  # store as comma-separated codes for simplicity; or use ARRAY on PG
    disliked_ingredients: Mapped[Optional[str]] = mapped_column(String)  # comma-separated or separate table

    target_kcal: Mapped[Optional[int]] = mapped_column()
    target_protein_g: Mapped[Optional[int]] = mapped_column()
    target_fat_g: Mapped[Optional[int]] = mapped_column()
    target_carb_g: Mapped[Optional[int]] = mapped_column()

    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[UserAccount] = relationship(back_populates="preferences")


# --- Pydantic Schemas --------------------------------------------------------
# Tip: If you use pydantic v2, import from pydantic import BaseModel, ConfigDict and set model_config
try:
    from pydantic import BaseModel, Field, ConfigDict
    P2 = True
except Exception:  # pragma: no cover
    from pydantic import BaseModel, Field  # type: ignore
    P2 = False


class ProfileBase(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = Field(None, description="female|male|other|unspecified")
    birth_date: Optional[date] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    country: Optional[str] = None
    locale: Optional[str] = "en"

    if P2:
        model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: str
    password: Optional[str] = None

    if P2:
        model_config = ConfigDict(from_attributes=True)


class UserRead(BaseModel):
    id: str
    email: str
    status: str
    created_at: datetime

    if P2:
        model_config = ConfigDict(from_attributes=True)


class UserProfileRead(ProfileBase):
    id: str
    user_id: str


class UserHealthMeasureIn(BaseModel):
    measure_date: date
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None
    bmr: Optional[float] = None
    activity_level: Optional[str] = None

    if P2:
        model_config = ConfigDict(from_attributes=True)


class UserHealthMeasureRead(UserHealthMeasureIn):
    id: str
    user_id: str
    created_at: datetime


class UserPreferenceIn(BaseModel):
    goal_type: Optional[str] = None
    diet_type: Optional[str] = None
    allergy_codes: Optional[List[str]] = None  # convert to comma-separated on persistence if not using ARRAY
    disliked_ingredients: Optional[List[str]] = None
    target_kcal: Optional[int] = None
    target_protein_g: Optional[int] = None
    target_fat_g: Optional[int] = None
    target_carb_g: Optional[int] = None

    if P2:
        model_config = ConfigDict(from_attributes=True)


class UserPreferenceRead(UserPreferenceIn):
    id: str
    user_id: str
    last_updated_at: datetime


# --- Utility converters ------------------------------------------------------
def list_to_csv(items: Optional[List[str]]) -> Optional[str]:
    return ",".join(items) if items else None


def csv_to_list(s: Optional[str]) -> Optional[List[str]]:
    if not s:
        return None
    return [x for x in (v.strip() for v in s.split(",")) if x]

