"""Feedback submission and listing endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Route, Feedback
from app.schemas import FeedbackCreate, FeedbackOut
from app.classifier import classify_comment

router = APIRouter(tags=["feedback"])


def _compute_severity(fb: FeedbackCreate) -> str:
    """Derive severity from the minimum sub-rating."""
    min_rating = min(
        fb.rating_overall, fb.rating_punctuality, fb.rating_cleanliness,
        fb.rating_crowding, fb.rating_driver_behaviour,
    )
    if min_rating <= 2:
        return "High"
    elif min_rating == 3:
        return "Medium"
    return "Low"


@router.post("/feedback", response_model=FeedbackOut, status_code=201)
def create_feedback(fb: FeedbackCreate, db: Session = Depends(get_db)):
    """Submit passenger feedback for a route/trip."""
    # Validate route exists
    route = db.query(Route).filter(Route.id == fb.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    # Auto-classify comment
    category = classify_comment(fb.comment) if fb.comment else None

    record = Feedback(
        route_id=fb.route_id,
        trip_id=fb.trip_id,
        rating_overall=fb.rating_overall,
        rating_punctuality=fb.rating_punctuality,
        rating_cleanliness=fb.rating_cleanliness,
        rating_crowding=fb.rating_crowding,
        rating_driver_behaviour=fb.rating_driver_behaviour,
        comment=fb.comment,
        category=category,
        severity=_compute_severity(fb),
        channel=fb.channel or "WEB",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/feedback", response_model=list[FeedbackOut])
def list_feedback(
    route_id: Optional[int] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List feedback with optional filters."""
    q = db.query(Feedback)

    if route_id:
        q = q.filter(Feedback.route_id == route_id)
    if category:
        q = q.filter(Feedback.category == category)
    if severity:
        q = q.filter(Feedback.severity == severity)
    if start_date:
        q = q.filter(Feedback.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        q = q.filter(Feedback.created_at <= datetime.fromisoformat(end_date))

    return q.order_by(Feedback.created_at.desc()).offset(offset).limit(limit).all()
