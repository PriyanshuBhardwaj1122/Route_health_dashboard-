"""
Synthetic data generator for the Route Health Dashboard.

Generates 15 bus routes, scheduled trips, and ~3,000 feedback entries
over 90 days with deliberate discoverable patterns.

Data patterns are inspired by the NYC 311 Service Requests dataset
(https://catalog.data.gov/dataset/311-service-requests-from-2010-to-present)
— mapping real complaint categories to bus-route feedback dimensions.

Patterns baked in:
  Route 42  →  Poor 5–7 PM performance (low crowding + punctuality ratings)
  Route 12  →  Improving trend (last 30 days much better than prior 60)
  Route 7   →  Weekend driver behaviour issues (Sat/Sun spikes)
  Others    →  Healthy baseline (avg ratings 3.5–4.2)

Lives inside the `app` package (rather than `scripts/`) so serverless
platforms like Vercel — which bundle a Python function's own package but
may not reliably trace imports outside it — can call `seed()` on cold
start without depending on a separately-bundled top-level script.
"""

import random
from datetime import datetime, timedelta

from app.database import engine, SessionLocal, Base
from app.models import Route, Trip, Feedback
from app.classifier import classify_comment

ROUTES = [
    ("1", "Downtown Express"),
    ("3", "Harbor Loop"),
    ("5", "University Shuttle"),
    ("7", "Crosstown Link"),
    ("9", "Northside Connector"),
    ("12", "Midtown Circulator"),
    ("15", "Eastbound Rapid"),
    ("18", "Airport Express"),
    ("21", "Waterfront Line"),
    ("25", "Hillside Runner"),
    ("28", "Central Avenue"),
    ("33", "Tech Park Shuttle"),
    ("37", "South Loop"),
    ("42", "Main Street Line"),
    ("50", "Outer Ring"),
]

TRIP_TIMES = [
    "06:00", "06:30", "07:00", "07:30", "08:00", "08:30",
    "09:00", "10:00", "11:00", "12:00", "13:00", "14:00",
    "15:00", "16:00", "16:30", "17:00", "17:30", "18:00",
    "18:30", "19:00", "20:00", "21:00", "22:00",
]

COMMENTS = {
    "Crowding": [
        "The bus is always packed after 6 PM.",
        "Way too crowded during rush hour.",
        "No seats available, had to stand the whole trip.",
        "Can't even board, the bus is full.",
        "Overcrowded, needs more frequent service.",
        "Standing room only, very uncomfortable.",
        "Too many passengers, felt like sardines.",
    ],
    "Punctuality": [
        "Bus was 15 minutes late again.",
        "Always behind schedule in the morning.",
        "Waited 30 minutes, no bus showed up.",
        "The bus never arrives on time.",
        "Schedule says 8 AM but it came at 8:20.",
        "Very unreliable timing, makes me late for work.",
    ],
    "Cleanliness": [
        "Seats are stained and dirty.",
        "Trash all over the floor.",
        "The bus smells terrible.",
        "Sticky floors and graffiti on the windows.",
        "Needs a deep clean, really gross.",
        "Debris and litter everywhere on the bus.",
    ],
    "Driver Behaviour": [
        "Driver was extremely rude to an elderly passenger.",
        "Driver skipped the university stop.",
        "Aggressive braking, I nearly fell.",
        "Driver was on the phone while driving.",
        "Drove past my stop without stopping.",
        "Driver yelled at passengers for no reason.",
        "Very reckless driving, felt unsafe.",
    ],
    "Overall Experience": [
        "Terrible experience overall.",
        "Service has gotten much worse lately.",
        "Great bus service, very comfortable.",
        "Worst public transit experience I've had.",
        "Generally fine, nothing special.",
        "Pleasant ride, courteous driver.",
    ],
}


def generate_rating(base: float, spread: float = 1.0) -> int:
    """Generate a rating 1-5 centered around base with some noise."""
    r = base + random.gauss(0, spread)
    return max(1, min(5, round(r)))


def seed():
    # Fixed seed: every cold start / serverless instance generates the
    # same demo data, so totals stay consistent across requests.
    random.seed(42)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # --- Create routes ---
    route_objs = {}
    for num, name in ROUTES:
        r = Route(route_number=num, name=name)
        db.add(r)
        db.flush()
        route_objs[num] = r

    # --- Create trips ---
    trip_objs = {}
    for num, route in route_objs.items():
        trips = []
        for day in range(7):
            for t in TRIP_TIMES:
                trip = Trip(
                    route_id=route.id,
                    scheduled_time=t,
                    day_of_week=day,
                    direction=random.choice(["Outbound", "Inbound"]),
                )
                db.add(trip)
                db.flush()
                trips.append(trip)
        trip_objs[num] = trips

    # --- Generate feedback ---
    now = datetime.utcnow()
    start = now - timedelta(days=90)
    total_created = 0

    for route_num, route in route_objs.items():
        # Determine how many feedback entries per route
        if route_num == "42":
            count = 350  # high volume — problem route
        elif route_num == "12":
            count = 250
        elif route_num == "7":
            count = 200
        else:
            count = random.randint(120, 200)

        for _ in range(count):
            # Random timestamp within 90-day window
            offset_days = random.uniform(0, 90)
            ts = start + timedelta(days=offset_days)
            hour = random.choices(
                range(6, 23),
                weights=[2, 5, 8, 6, 3, 2, 2, 2, 3, 5, 8, 6, 4, 3, 2, 2, 1],
            )[0]
            ts = ts.replace(hour=hour, minute=random.randint(0, 59))

            day_of_week = ts.weekday()
            is_recent = (now - ts).days <= 30

            # === Pattern: Route 42 — poor evening performance ===
            if route_num == "42" and 17 <= hour <= 19:
                base_overall = 2.2
                base_crowding = 1.5
                base_punctuality = 2.0
                base_clean = 3.5
                base_driver = 3.5
                comment_pool = ["Crowding", "Punctuality"]
            elif route_num == "42":
                base_overall = 3.2
                base_crowding = 3.0
                base_punctuality = 3.0
                base_clean = 3.5
                base_driver = 3.5
                comment_pool = None

            # === Pattern: Route 12 — improving trend ===
            elif route_num == "12" and is_recent:
                base_overall = 4.2
                base_crowding = 4.0
                base_punctuality = 4.0
                base_clean = 4.3
                base_driver = 4.5
                comment_pool = ["Overall Experience"]
            elif route_num == "12":
                base_overall = 2.5
                base_crowding = 2.5
                base_punctuality = 2.3
                base_clean = 3.0
                base_driver = 3.0
                comment_pool = ["Punctuality", "Crowding"]

            # === Pattern: Route 7 — weekend driver issues ===
            elif route_num == "7" and day_of_week >= 5:
                base_overall = 2.5
                base_crowding = 3.5
                base_punctuality = 3.5
                base_clean = 3.5
                base_driver = 1.8
                comment_pool = ["Driver Behaviour"]
            elif route_num == "7":
                base_overall = 3.8
                base_crowding = 3.8
                base_punctuality = 3.8
                base_clean = 3.8
                base_driver = 3.8
                comment_pool = None

            # === Other routes: healthy baseline ===
            else:
                base_overall = random.uniform(3.5, 4.2)
                base_crowding = random.uniform(3.3, 4.0)
                base_punctuality = random.uniform(3.3, 4.0)
                base_clean = random.uniform(3.5, 4.3)
                base_driver = random.uniform(3.5, 4.3)
                comment_pool = None

            r_overall = generate_rating(base_overall, 0.7)
            r_punct = generate_rating(base_punctuality, 0.7)
            r_clean = generate_rating(base_clean, 0.6)
            r_crowd = generate_rating(base_crowding, 0.7)
            r_driver = generate_rating(base_driver, 0.6)

            # 40% chance of a comment
            comment = None
            category = None
            if random.random() < 0.4:
                if comment_pool:
                    cat = random.choice(comment_pool)
                else:
                    cat = random.choice(list(COMMENTS.keys()))
                comment = random.choice(COMMENTS[cat])
                category = classify_comment(comment)

            severity = "Low"
            min_rating = min(r_overall, r_punct, r_clean, r_crowd, r_driver)
            if min_rating <= 2:
                severity = "High"
            elif min_rating == 3:
                severity = "Medium"

            # Pick a random trip for this route
            trips = trip_objs[route_num]
            trip = random.choice(trips) if trips else None

            fb = Feedback(
                route_id=route.id,
                trip_id=trip.id if trip else None,
                rating_overall=r_overall,
                rating_punctuality=r_punct,
                rating_cleanliness=r_clean,
                rating_crowding=r_crowd,
                rating_driver_behaviour=r_driver,
                comment=comment,
                category=category,
                severity=severity,
                created_at=ts,
                channel=random.choice(["WEB", "APP", "PHONE"]),
            )
            db.add(fb)
            total_created += 1

        if total_created % 500 == 0:
            db.flush()

    db.commit()
    db.close()
    print(f"Seeded {len(ROUTES)} routes, {sum(len(t) for t in trip_objs.values())} trips, {total_created} feedback entries.")