"""Pydantic request/response models — Public Transport Feedback Platform."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Route schemas
# ---------------------------------------------------------------------------

class RouteOut(BaseModel):
    id: int
    route_number: str
    name: str
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Feedback schemas
# ---------------------------------------------------------------------------

class FeedbackCreate(BaseModel):
    """Passenger submits a rating for a route/trip."""
    route_id: int
    trip_id: Optional[int] = None
    rating_overall: int = Field(..., ge=1, le=5)
    rating_punctuality: int = Field(..., ge=1, le=5)
    rating_cleanliness: int = Field(..., ge=1, le=5)
    rating_crowding: int = Field(..., ge=1, le=5)
    rating_driver_behaviour: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    channel: Optional[str] = "WEB"


class FeedbackOut(BaseModel):
    id: int
    route_id: int
    trip_id: Optional[int] = None
    rating_overall: int
    rating_punctuality: int
    rating_cleanliness: int
    rating_crowding: int
    rating_driver_behaviour: int
    comment: Optional[str] = None
    category: Optional[str] = None
    severity: str
    created_at: datetime
    channel: Optional[str] = None
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Analytics schemas
# ---------------------------------------------------------------------------

class RouteHealth(BaseModel):
    """Health snapshot for a single route."""
    route_id: int
    route_number: str
    overall_rating: float          # 1.0–5.0
    top_issue: str
    second_issue: str
    worst_period: str              # e.g. "5 PM–7 PM"
    complaints_this_month: int
    total_feedback: int
    health_score: float            # 0–100


class TrendCategory(BaseModel):
    category: str
    recent_avg: float
    prior_avg: float
    delta: float
    direction: str  # improving / declining / stable


class TrendResponse(BaseModel):
    route_number: str
    trends: list[TrendCategory]


class SeverityBreakdown(BaseModel):
    Low: int = 0
    Medium: int = 0
    High: int = 0


class HeatmapCell(BaseModel):
    hour: int
    day_of_week: int
    count: int
    avg_rating: float


class CategoryBreakdown(BaseModel):
    category: str
    count: int
    pct: float


class ClassifyRequest(BaseModel):
    comment: str


class ClassifyResponse(BaseModel):
    category: str
    confidence: str = "keyword-match"
