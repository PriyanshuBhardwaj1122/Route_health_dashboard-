# Route Health Dashboard

A commuter feedback and bus-operations analytics system for city bus operators. Passengers submit per-trip ratings and free-text comments; administrators view analytics that surface recurring problems by route, time, category, and severity.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Browser                               │
│  ┌────────────────────┐   ┌─────────────────────────────┐   │
│  │  index.html        │   │  dashboard.html              │   │
│  │  Passenger Form    │   │  Admin Analytics + Chart.js  │   │
│  └────────┬───────────┘   └──────────┬──────────────────┘   │
│           │ POST /feedback            │ GET /analytics/*     │
└───────────┼───────────────────────────┼──────────────────────┘
            │                           │
┌───────────▼───────────────────────────▼──────────────────────┐
│                     FastAPI (Uvicorn)                         │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ Routes CRUD │  │ Feedback API │  │  Analytics Engine  │  │
│  │             │  │ + Classifier │  │  (pandas)          │  │
│  └──────┬──────┘  └──────┬───────┘  └────────┬───────────┘  │
│         │                │                    │              │
│         └────────────────┼────────────────────┘              │
│                          │                                   │
│              ┌───────────▼───────────┐                       │
│              │   SQLAlchemy ORM      │                       │
│              │   SQLite (data.db)    │                       │
│              └───────────────────────┘                       │
└──────────────────────────────────────────────────────────────┘
```

## Quick Start

### Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate synthetic data (15 routes, 90 days of history)
python scripts/seed_data.py

# 3. Start the server
uvicorn app.main:app --reload

# Open http://localhost:8000 (feedback form)
# Open http://localhost:8000/dashboard.html (admin dashboard)
```

### Docker

```bash
# Build and run — seeds data automatically on first boot
docker build -t route-health-dashboard .
docker run -p 8000:8000 route-health-dashboard
```

### Running Tests

```bash
pytest tests/test_api.py -v
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/routes` | List all routes |
| `GET` | `/routes/{id}` | Get single route |
| `POST` | `/feedback` | Submit passenger feedback (5 sub-ratings + optional comment) |
| `GET` | `/feedback` | List feedback (filterable: `route_id`, `category`, `severity`, `start_date`, `end_date`, `limit`, `offset`) |
| `GET` | `/analytics/route/{id}` | Route health snapshot (rating, top issues, worst period, complaint count) |
| `GET` | `/analytics/rankings` | All routes ranked by overall rating (worst first) |
| `GET` | `/analytics/trends/{id}` | 30-day vs prior 30-day trend per category |
| `GET` | `/analytics/severity-breakdown` | Count by severity level (optional `route_id` filter) |
| `GET` | `/analytics/heatmap` | Feedback volume & avg rating by hour × day-of-week |
| `GET` | `/analytics/categories` | Comment category breakdown (optional `route_id` filter) |
| `POST` | `/classify` | Classify a free-text comment into a category |

### Example: Route Analytics Response

```json
{
  "route_number": "42",
  "overall_rating": 2.7,
  "top_issue": "Crowding",
  "second_issue": "Punctuality",
  "worst_period": "5 PM–7 PM",
  "complaints_this_month": 128
}
```

## Dataset

Complaint categories and feedback patterns are inspired by the [NYC 311 Service Requests dataset](https://catalog.data.gov/dataset/311-service-requests-from-2010-to-present). The seed script generates synthetic data with realistic distributions mapped to bus-route feedback dimensions.

## Tech Stack

- **Backend:** Python 3.11, FastAPI, Uvicorn
- **Database:** SQLite via SQLAlchemy ORM
- **Analytics:** pandas
- **Frontend:** HTML + vanilla JS + Chart.js (CDN)
- **Classifier:** Rule-based keyword matcher (pure Python, fully offline)
- **Deployment:** Single Docker container (Render/Railway compatible)

## Synthetic Data Patterns

The seed script generates deliberate, discoverable patterns:

| Route | Pattern | What to look for |
|-------|---------|------------------|
| **42** | Poor 5–7 PM performance | Low crowding + punctuality ratings in evening rush |
| **12** | Improving trend | Last 30 days significantly better than prior 60 |
| **7** | Weekend driver issues | Driver behaviour complaints spike on Sat/Sun |
| Others | Healthy baseline | Ratings averaging 3.5–4.2 |

## Known Limitations / Next Steps

- **Classifier is rule-based.** The keyword matcher handles common patterns well but could be upgraded to an LLM-based classifier without changing the API contract (`POST /classify` response shape stays the same).
- **Authentication** is not implemented. In production, admin endpoints should be protected.
- **Database** is SQLite for zero-dependency deployment. For production scale, migrate to PostgreSQL by changing the `DATABASE_URL` environment variable.
- **Chart.js is CDN-hosted.** This is the only external network dependency at runtime.
