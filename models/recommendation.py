"""
Fitmealor models/recommendation.py
- SQLAlchemy models for recommendation sessions, items, interactions, feedback, feature snapshot
- Pydantic DTOs
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Any
import uuid

from sqlalchemy import (
    String, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint, JSON
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


# --- SQLAlchemy Base ---------------------------------------------------------
class Base(DeclarativeBase):
    pass


class RecommendationSession(Base):
    __tablename__ = "recommendation_session"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    algo_version: Mapped[Optional[str]] = mapped_column(String(64))
    input_context: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[List["RecommendationItem"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    features: Mapped[List["AlgoFeatureSnapshot"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class RecommendationItem(Base):
    __tablename__ = "recommendation_item"
    __table_args__ = (
        UniqueConstraint("session_id", "meal_id", name="uq_rec_item_once_per_meal_in_session"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("recommendation_session.id", ondelete="CASCADE"), index=True)
    meal_id: Mapped[str] = mapped_column(String(36), index=True)

    rank: Mapped[int] = mapped_column(Integer)
    score: Mapped[float] = mapped_column(Numeric(8, 4))
    filter_applied: Mapped[Optional[dict]] = mapped_column(JSON)

    session: Mapped[RecommendationSession] = relationship(back_populates="items")
    feedbacks: Mapped[List["RatingFeedback"]] = relationship(back_populates="session_item", cascade="all, delete-orphan")


class UserInteraction(Base):
    __tablename__ = "user_interaction"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    meal_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)

    event_type: Mapped[str] = mapped_column(String(20))  # impress|click|save|add_to_cart|purchase
    event_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class RatingFeedback(Base):
    __tablename__ = "rating_feedback"
    __table_args__ = (
        UniqueConstraint("user_id", "session_item_id", name="uq_feedback_once_per_user_item"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    session_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("recommendation_item.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int] = mapped_column(Integer)  # 1..5
    comment: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session_item: Mapped[RecommendationItem] = relationship(back_populates="feedbacks")


class AlgoFeatureSnapshot(Base):
    __tablename__ = "algo_feature_snapshot"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("recommendation_session.id", ondelete="CASCADE"), index=True)
    feature_type: Mapped[str] = mapped_column(String(20))  # user|meal|pair|context
    feature_payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[RecommendationSession] = relationship(back_populates="features")


# --- Pydantic Schemas --------------------------------------------------------
try:
    from pydantic import BaseModel, Field, ConfigDict
    P2 = True
except Exception:  # pragma: no cover
    from pydantic import BaseModel, Field  # type: ignore
    P2 = False


class RecoContext(BaseModel):
    time: Optional[str] = None  # breakfast|lunch|dinner|snack
    remaining_kcal: Optional[int] = None
    locale: Optional[str] = None

    if P2:
        model_config = ConfigDict(from_attributes=True)


class RecoRequest(BaseModel):
    user_id: str
    context: Optional[RecoContext] = None


class RecoItemDTO(BaseModel):
    meal_id: str
    rank: int
    score: float
    filter_applied: Optional[dict] = None

    if P2:
        model_config = ConfigDict(from_attributes=True)


class RecoResponse(BaseModel):
    session_id: str
    items: List[RecoItemDTO]


class InteractionIn(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    meal_id: Optional[str] = None
    event_type: str

    if P2:
        model_config = ConfigDict(from_attributes=True)


class FeedbackIn(BaseModel):
    user_id: str
    session_item_id: str
    rating: int
    comment: Optional[str] = None

    if P2:
        model_config = ConfigDict(from_attributes=True)

