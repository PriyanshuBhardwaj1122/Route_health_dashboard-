"""Analytics endpoints — route health, rankings, trends, heatmap."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Route
from app.schemas import (
    RouteHealth, TrendResponse, SeverityBreakdown,
    HeatmapCell, CategoryBreakdown,
    ClassifyRequest, ClassifyResponse,
)
from app.analytics_engine import (
    get_route_health, get_all_rankings,
    get_route_trends, get_severity_breakdown,
    get_heatmap_data, get_category_breakdown,
)
from app.classifier import classify_comment

router = APIRouter(tags=["analytics"])


def _validate_route(route_id: int, db: Session) -> Route:
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route


@router.get("/analytics/route/{route_id}", response_model=RouteHealth)
def route_health(route_id: int, db: Session = Depends(get_db)):
    _validate_route(route_id, db)
    return get_route_health(route_id, db)


@router.get("/analytics/rankings", response_model=list[RouteHealth])
def rankings(db: Session = Depends(get_db)):
    return get_all_rankings(db)


@router.get("/analytics/trends/{route_id}", response_model=TrendResponse)
def trends(route_id: int, db: Session = Depends(get_db)):
    _validate_route(route_id, db)
    return get_route_trends(route_id, db)


@router.get("/analytics/severity-breakdown", response_model=SeverityBreakdown)
def severity_breakdown(route_id: Optional[int] = None, db: Session = Depends(get_db)):
    return get_severity_breakdown(db, route_id)


@router.get("/analytics/heatmap", response_model=list[HeatmapCell])
def heatmap(route_id: Optional[int] = None, db: Session = Depends(get_db)):
    return get_heatmap_data(db, route_id)


@router.get("/analytics/categories", response_model=list[CategoryBreakdown])
def categories(route_id: Optional[int] = None, db: Session = Depends(get_db)):
    return get_category_breakdown(db, route_id)


@router.post("/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest):
    category = classify_comment(req.comment)
    return ClassifyResponse(category=category)
