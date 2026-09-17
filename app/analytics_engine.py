"""
pandas-based analytics engine for the Public Transport Feedback Platform.

Computes route health scores, rankings, trends, severity breakdowns,
heatmaps, and category distributions.
"""

from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session

from app.models import Route, Feedback
from app.schemas import (
    RouteHealth, TrendResponse, TrendCategory,
    SeverityBreakdown, HeatmapCell, CategoryBreakdown,
)

TREND_THRESHOLD = 0.15  # ±0.15 avg-rating change = stable


def _feedback_df(db: Session, route_id: int = None) -> pd.DataFrame:
    """Load feedback into a DataFrame, optionally filtered by route."""
    q = db.query(Feedback)
    if route_id:
        q = q.filter(Feedback.route_id == route_id)
    rows = q.all()
    if not rows:
        return pd.DataFrame()
    data = [
        {
            "id": f.id,
            "route_id": f.route_id,
            "rating_overall": f.rating_overall,
            "rating_punctuality": f.rating_punctuality,
            "rating_cleanliness": f.rating_cleanliness,
            "rating_crowding": f.rating_crowding,
            "rating_driver_behaviour": f.rating_driver_behaviour,
            "comment": f.comment,
            "category": f.category,
            "severity": f.severity,
            "created_at": f.created_at,
        }
        for f in rows
    ]
    return pd.DataFrame(data)


def _format_hour_range(start_hour: int) -> str:
    """Format a 2-hour window as 'H AM/PM–H AM/PM'."""
    def fmt(h):
        if h == 0 or h == 24:
            return "12 AM"
        elif h == 12:
            return "12 PM"
        elif h < 12:
            return f"{h} AM"
        else:
            return f"{h - 12} PM"
    return f"{fmt(start_hour)}–{fmt(start_hour + 2)}"


def _sub_category_avgs(df: pd.DataFrame) -> dict[str, float]:
    """Average sub-ratings → category name map."""
    return {
        "Crowding": df["rating_crowding"].mean(),
        "Punctuality": df["rating_punctuality"].mean(),
        "Cleanliness": df["rating_cleanliness"].mean(),
        "Driver Behaviour": df["rating_driver_behaviour"].mean(),
    }


def get_route_health(route_id: int, db: Session) -> RouteHealth:
    """Compute health snapshot for a single route."""
    route = db.query(Route).filter(Route.id == route_id).first()
    df = _feedback_df(db, route_id)

    if df.empty:
        return RouteHealth(
            route_id=route_id, route_number=route.route_number,
            overall_rating=0.0, top_issue="N/A", second_issue="N/A",
            worst_period="N/A", complaints_this_month=0,
            total_feedback=0, health_score=100.0,
        )

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    overall_rating = round(df["rating_overall"].mean(), 1)
    total = len(df)
    this_month = int((df["created_at"] >= month_start).sum())

    # Top issues = two lowest-scoring sub-categories
    avgs = _sub_category_avgs(df)
    sorted_cats = sorted(avgs, key=avgs.get)
    top_issue = sorted_cats[0]
    second_issue = sorted_cats[1] if len(sorted_cats) > 1 else "N/A"

    # Worst period: 2-hour bucket with lowest average overall rating (min 5 samples)
    df["hour"] = df["created_at"].dt.hour
    df["bucket"] = (df["hour"] // 2) * 2
    bucket_stats = df.groupby("bucket").agg(
        avg=("rating_overall", "mean"), cnt=("id", "count")
    )
    valid_buckets = bucket_stats[bucket_stats["cnt"] >= 5]
    if not valid_buckets.empty:
        worst_bucket = int(valid_buckets["avg"].idxmin())
        worst_period = _format_hour_range(worst_bucket)
    else:
        worst_period = "N/A"

    # Health score: overall_rating mapped to 0-100
    health_score = round(max(0, min(100, (overall_rating - 1) / 4 * 100)), 1)

    return RouteHealth(
        route_id=route_id,
        route_number=route.route_number,
        overall_rating=overall_rating,
        top_issue=top_issue,
        second_issue=second_issue,
        worst_period=worst_period,
        complaints_this_month=this_month,
        total_feedback=total,
        health_score=health_score,
    )


def get_all_rankings(db: Session) -> list[RouteHealth]:
    """All routes ranked by overall_rating ascending (worst first)."""
    routes = db.query(Route).all()
    results = [get_route_health(r.id, db) for r in routes]
    results.sort(key=lambda x: x.overall_rating)
    return results


def get_route_trends(route_id: int, db: Session) -> TrendResponse:
    """Compare trailing 30-day vs prior 30-day avg ratings per sub-category."""
    route = db.query(Route).filter(Route.id == route_id).first()
    df = _feedback_df(db, route_id)
    now = datetime.utcnow()
    cutoff_recent = now - timedelta(days=30)
    cutoff_prior = now - timedelta(days=60)

    recent = df[df["created_at"] >= cutoff_recent]
    prior = df[(df["created_at"] >= cutoff_prior) & (df["created_at"] < cutoff_recent)]

    rating_cols = {
        "Crowding": "rating_crowding",
        "Punctuality": "rating_punctuality",
        "Cleanliness": "rating_cleanliness",
        "Driver Behaviour": "rating_driver_behaviour",
        "Overall": "rating_overall",
    }

    trends = []
    for cat, col in rating_cols.items():
        recent_avg = round(recent[col].mean(), 2) if not recent.empty else 0.0
        prior_avg = round(prior[col].mean(), 2) if not prior.empty else 0.0
        delta = round(recent_avg - prior_avg, 2)

        if delta > TREND_THRESHOLD:
            direction = "improving"
        elif delta < -TREND_THRESHOLD:
            direction = "declining"
        else:
            direction = "stable"

        trends.append(TrendCategory(
            category=cat, recent_avg=recent_avg,
            prior_avg=prior_avg, delta=delta, direction=direction,
        ))

    return TrendResponse(route_number=route.route_number, trends=trends)


def get_severity_breakdown(db: Session, route_id: int = None) -> SeverityBreakdown:
    """Count feedback by severity level."""
    df = _feedback_df(db, route_id)
    if df.empty:
        return SeverityBreakdown()
    counts = df["severity"].value_counts().to_dict()
    return SeverityBreakdown(
        Low=counts.get("Low", 0),
        Medium=counts.get("Medium", 0),
        High=counts.get("High", 0),
    )


def get_heatmap_data(db: Session, route_id: int = None) -> list[HeatmapCell]:
    """Feedback volume and avg rating by hour × day-of-week."""
    df = _feedback_df(db, route_id)
    if df.empty:
        return []

    df["hour"] = df["created_at"].dt.hour
    df["day_of_week"] = df["created_at"].dt.dayofweek

    grouped = df.groupby(["hour", "day_of_week"]).agg(
        count=("id", "count"),
        avg_rating=("rating_overall", "mean"),
    ).reset_index()

    return [
        HeatmapCell(
            hour=int(row["hour"]),
            day_of_week=int(row["day_of_week"]),
            count=int(row["count"]),
            avg_rating=round(row["avg_rating"], 2),
        )
        for _, row in grouped.iterrows()
    ]


def get_category_breakdown(db: Session, route_id: int = None) -> list[CategoryBreakdown]:
    """Complaint count and percentage per auto-classified category."""
    df = _feedback_df(db, route_id)
    if df.empty:
        return []
    has_cat = df[df["category"].notna()]
    if has_cat.empty:
        return []
    counts = has_cat["category"].value_counts()
    total = counts.sum()
    return [
        CategoryBreakdown(category=cat, count=int(cnt), pct=round(cnt / total * 100, 1))
        for cat, cnt in counts.items()
    ]
