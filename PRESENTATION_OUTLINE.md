# Route Health Dashboard — Presentation Outline

## Slide 1: Problem Statement

**Title:** City Bus Passengers Deserve Better — But Operators Are Flying Blind

- Passengers have no easy channel to report service issues
- Operators lack data to identify which routes need attention and when
- Problems like chronic overcrowding or rude drivers go undetected until they become crises
- No visibility into whether fixes are actually working

---

## Slide 2: Solution Overview

**Title:** Route Health Dashboard — Feedback-Driven Operations Analytics

- **Passenger-facing:** Simple mobile-friendly form to rate any trip across 5 dimensions
- **Operator-facing:** Real-time dashboard showing route rankings, trend detection, and heatmaps
- **Bonus AI:** Automatic free-text comment classification (Crowding, Punctuality, Cleanliness, Driver Behaviour)
- Single deployable container — zero infrastructure overhead

---

## Slide 3: Architecture

**Title:** How It's Built

- FastAPI backend serving both API and frontend
- SQLite database (zero-config, swap to Postgres for production)
- pandas-powered analytics engine computing rankings, trends, and time-based patterns
- Rule-based NLP classifier for comment categorization
- Chart.js dashboards — no framework overhead
- Docker single-container deployment (Render/Railway ready)

---

## Slide 4: Data Model

**Title:** Three-Table Design

- **Route** → route_number, name
- **Trip** → route_id, scheduled_time, day_of_week
- **Feedback** → 5 sub-ratings, free-text comment, auto-classified category, computed severity
- Severity derived from lowest sub-rating (≤2 = High, 3 = Medium, ≥4 = Low)

---

## Slide 5: Dataset

**Title:** Inspired by NYC 311 Service Requests

- Real-world complaint patterns from NYC 311 dataset (https://catalog.data.gov/dataset/311-service-requests-from-2010-to-present)
- Categories mapped to bus feedback dimensions: Crowding, Punctuality, Cleanliness, Driver Behaviour
- Synthetic data seed script generates deliberate patterns for demo

---

## Slide 6: Live Demo — Route 42 (The Problem Route)

**Title:** Identifying Chronic Issues

- Navigate to Admin Dashboard → Route 42 is ranked worst
- Click Route 42 to see:
  - **Overall Rating: ~2.7/5**
  - **Top Issue: Crowding** / Second Issue: Punctuality
  - **Worst Period: 5 PM–7 PM** (evening rush)
  - Sub-rating bar chart shows crowding and punctuality both red
  - Severity donut is majority High
- **Insight:** This route needs additional buses deployed during evening rush

---

## Slide 7: Live Demo — Route 12 (The Improving Route)

**Title:** Tracking Whether Fixes Work

- Click Route 12 in the rankings table
- Open the Trend panel:
  - All categories show **"improving"** with significant positive deltas
  - Last 30 days averaging ~4.0 vs prior 30 days at ~2.8
- **Insight:** Whatever intervention was applied to Route 12 is measurably working

---

## Slide 8: Live Demo — Route 7 (Weekend Pattern)

**Title:** Time-Based Anomaly Detection

- Route 7 shows driver behaviour complaints concentrated on weekends
- The heatmap visualization reveals the Sat/Sun pattern
- **Insight:** Likely a specific weekend driver or crew — scheduling intervention needed

---

## Slide 9: The Bonus AI — Comment Classifier

**Title:** Turning Unstructured Text Into Actionable Categories

- Demo: Submit "The bus is always packed after 6 PM." → **Crowding**
- Demo: Submit "Driver skipped the university stop." → **Driver Behaviour**
- Rule-based keyword matcher — runs offline, zero latency, no API keys
- Categories: Crowding, Punctuality, Cleanliness, Driver Behaviour, Overall Experience, Other
- Designed to be swapped for an LLM classifier without changing the API contract

---

## Slide 10: Analytics Approach

**Title:** How We Compute Route Health

- **Overall rating:** Mean of rating_overall across all feedback
- **Top/second issue:** Two lowest-scoring sub-category averages
- **Worst period:** 2-hour time bucket with lowest average rating (min 5 samples)
- **Trends:** 30-day rolling comparison with ±0.15 threshold for stable/improving/declining
- **Severity:** Derived from minimum sub-rating per feedback entry
- All computed in pandas — transparent, auditable, fast at this scale

---

## Slide 11: Tech Stack Summary

**Title:** Simple Stack, Production-Ready

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | FastAPI + Uvicorn | Async, auto-docs, fast |
| Database | SQLite + SQLAlchemy | Zero-config, ORM for portability |
| Analytics | pandas | Industry standard, transparent |
| Frontend | HTML + JS + Chart.js | No build step, fast to ship |
| Classifier | Keyword matcher | Offline, instant, swappable |
| Deploy | Docker single container | One command, Render/Railway ready |

---

## Slide 12: What We'd Build Next

**Title:** Roadmap

1. **LLM-based classifier** — swap keyword matcher for a fine-tuned model for higher accuracy
2. **Real-time alerts** — notify operators when a route's rating drops below a threshold
3. **Authentication & roles** — passenger accounts, admin login
4. **PostgreSQL migration** — for production scale
5. **Trip-level GPS tracking** — match feedback to specific vehicles
6. **Predictive analytics** — forecast which routes are likely to deteriorate
7. **Multi-language support** — classify comments in multiple languages

---

## Slide 13: Thank You

**Title:** Questions?

- Live app running at: [deployment URL]
- GitHub: [repository link]
- API documentation auto-generated at `/docs` (FastAPI Swagger UI)
