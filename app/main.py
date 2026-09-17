"""FastAPI application — Route Health Dashboard."""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base, SessionLocal
from app.models import Route
from app.routers import routes, feedback, analytics

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Self-seed on cold start if the database is empty. This makes the app
# work correctly on serverless platforms (e.g. Vercel) regardless of
# whether a pre-built data.db was successfully bundled with the function —
# the app populates its own demo data the first time it runs.
def _seed_if_empty():
    db = SessionLocal()
    try:
        if db.query(Route).count() == 0:
            from scripts.seed_data import seed
            seed()
    finally:
        db.close()

_seed_if_empty()

app = FastAPI(
    title="Route Health Dashboard",
    description="Public Transport Feedback & Service Analytics — passenger ratings, route health scores, trend detection, and AI-powered comment classification.",
    version="1.0.0",
)

# --- API routers ---
app.include_router(routes.router)
app.include_router(feedback.router)
app.include_router(analytics.router)

# --- Static files (frontend) — mounted last so API routes take priority ---
# Resolve static dir relative to project root (works both locally and on Vercel)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_static_dir = os.path.join(_project_root, "static")

if os.path.isdir(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")