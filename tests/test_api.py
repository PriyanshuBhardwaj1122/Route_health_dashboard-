"""Smoke tests for every API endpoint — Route Health Dashboard."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ─── Routes ──────────────────────────────────────────────

def test_list_routes():
    res = client.get("/routes")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 15
    assert "route_number" in data[0]
    assert "name" in data[0]


def test_get_route():
    res = client.get("/routes/1")
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert "route_number" in data


def test_get_route_not_found():
    res = client.get("/routes/9999")
    assert res.status_code == 404


# ─── Feedback ────────────────────────────────────────────

def test_create_feedback():
    payload = {
        "route_id": 1,
        "rating_overall": 3,
        "rating_punctuality": 2,
        "rating_cleanliness": 4,
        "rating_crowding": 1,
        "rating_driver_behaviour": 3,
        "comment": "Way too crowded during rush hour.",
    }
    res = client.post("/feedback", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["route_id"] == 1
    assert data["category"] == "Crowding"
    assert data["severity"] == "High"
    assert data["comment"] == "Way too crowded during rush hour."


def test_create_feedback_no_comment():
    payload = {
        "route_id": 1,
        "rating_overall": 4,
        "rating_punctuality": 4,
        "rating_cleanliness": 5,
        "rating_crowding": 4,
        "rating_driver_behaviour": 5,
    }
    res = client.post("/feedback", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["category"] is None
    assert data["severity"] == "Low"


def test_create_feedback_invalid_route():
    payload = {
        "route_id": 9999,
        "rating_overall": 3,
        "rating_punctuality": 3,
        "rating_cleanliness": 3,
        "rating_crowding": 3,
        "rating_driver_behaviour": 3,
    }
    res = client.post("/feedback", json=payload)
    assert res.status_code == 404


def test_list_feedback():
    res = client.get("/feedback")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) <= 50  # default limit


def test_list_feedback_filtered():
    res = client.get("/feedback?route_id=1&severity=High&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) <= 10
    for item in data:
        assert item["route_id"] == 1
        assert item["severity"] == "High"


# ─── Analytics ───────────────────────────────────────────

def test_route_analytics():
    res = client.get("/analytics/route/1")
    assert res.status_code == 200
    data = res.json()
    required_keys = ["route_number", "overall_rating", "top_issue",
                     "second_issue", "worst_period", "complaints_this_month"]
    for key in required_keys:
        assert key in data, f"Missing key: {key}"
    assert isinstance(data["overall_rating"], float)
    assert isinstance(data["complaints_this_month"], int)


def test_route_analytics_not_found():
    res = client.get("/analytics/route/9999")
    assert res.status_code == 404


def test_rankings():
    res = client.get("/analytics/rankings")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 15
    # Should be sorted ascending by overall_rating
    ratings = [r["overall_rating"] for r in data]
    assert ratings == sorted(ratings)


def test_trends():
    res = client.get("/analytics/trends/1")
    assert res.status_code == 200
    data = res.json()
    assert "route_number" in data
    assert "trends" in data
    assert isinstance(data["trends"], list)
    for trend in data["trends"]:
        assert "category" in trend
        assert "direction" in trend
        assert trend["direction"] in ("improving", "declining", "stable")


def test_severity_breakdown():
    res = client.get("/analytics/severity-breakdown")
    assert res.status_code == 200
    data = res.json()
    assert "Low" in data
    assert "Medium" in data
    assert "High" in data


def test_severity_breakdown_by_route():
    res = client.get("/analytics/severity-breakdown?route_id=1")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data["High"], int)


def test_heatmap():
    res = client.get("/analytics/heatmap")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    cell = data[0]
    assert "hour" in cell
    assert "day_of_week" in cell
    assert "count" in cell
    assert "avg_rating" in cell


# ─── Classifier ──────────────────────────────────────────

def test_classify_crowding():
    res = client.post("/classify", json={"comment": "The bus is always packed after 6 PM."})
    assert res.status_code == 200
    data = res.json()
    assert data["category"] == "Crowding"
    assert data["confidence"] == "keyword-match"


def test_classify_driver():
    res = client.post("/classify", json={"comment": "Driver skipped the university stop."})
    assert res.status_code == 200
    data = res.json()
    assert data["category"] == "Driver Behaviour"


def test_classify_other():
    res = client.post("/classify", json={"comment": "xyz abc 123"})
    assert res.status_code == 200
    data = res.json()
    assert data["category"] == "Other"


# ─── Static files ────────────────────────────────────────

def test_index_page():
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]


def test_dashboard_page():
    res = client.get("/dashboard.html")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
