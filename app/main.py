"""FastAPI application — Route Health Dashboard."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.routers import routes, feedback, analytics

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

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
app.mount("/", StaticFiles(directory="static", html=True), name="static")
