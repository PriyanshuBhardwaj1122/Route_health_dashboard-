"""SQLAlchemy ORM models — Public Transport Feedback & Service Analytics."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Route(Base):
    """A bus route operated by the transit authority."""
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    route_number = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)

    trips = relationship("Trip", back_populates="route")
    feedbacks = relationship("Feedback", back_populates="route")


class Trip(Base):
    """A scheduled trip on a specific route."""
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    scheduled_time = Column(String, nullable=False)   # "HH:MM"
    day_of_week = Column(Integer, nullable=False)      # 0=Mon … 6=Sun
    direction = Column(String, default="Outbound")

    route = relationship("Route", back_populates="trips")
    feedbacks = relationship("Feedback", back_populates="trip")


class Feedback(Base):
    """Passenger feedback/rating for a trip or route."""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True)

    # Sub-ratings (1–5 stars)
    rating_overall = Column(Integer, nullable=False)
    rating_punctuality = Column(Integer, nullable=False)
    rating_cleanliness = Column(Integer, nullable=False)
    rating_crowding = Column(Integer, nullable=False)
    rating_driver_behaviour = Column(Integer, nullable=False)

    comment = Column(Text, nullable=True)
    category = Column(String, nullable=True)   # auto-classified from comment
    severity = Column(String, nullable=False)   # High / Medium / Low
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    channel = Column(String, default="WEB")     # WEB, PHONE, APP

    route = relationship("Route", back_populates="feedbacks")
    trip = relationship("Trip", back_populates="feedbacks")
