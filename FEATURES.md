# AroundU Backend – Feature Documentation

## Overview
The **AroundU** platform provides a comprehensive backend that powers a location‑based discovery service. It combines AI‑driven services, robust REST APIs for mobile and dashboard clients, and analytics dashboards for owners and admins.

---

## Core Features

1. **AI Chatbot (RAG‑based)**
   - **Purpose**: Conversational assistant that suggests places based on user context.
   - **Implementation**: `src/services/chatbot_service.py`
   - **Key Methods**:
     - `chat(user_id, query)`: Retrieves relevant places from the DB, injects them into the prompt, calls the external LLM via HuggingFace, and returns a grounded response.
   - **Endpoints**:
     - `POST /owner/chatbot/query` – accepts `{ "user_id": int, "query": string }` and returns `{ "response": string, "sources": [...] }`.

2. **Recommendation Engine**
   - **Purpose**: Provide personalized place recommendations.
   - **Implementation**: `src/services/recommendation_service.py`
   - **Scoring**:
     - Rating (50 %) – Bayesian average.
     - Distance (30 %) – Reciprocal distance decay.
     - Favorites (20 %) – User‑saved places.
   - **Endpoints**:
     - `GET /owner/recommendations?user_id={id}&limit={n}` – returns a list of recommended places.

3. **Anomaly Detection (AI‑based)**
   - **Purpose**: Detect out‑of‑order user behaviour (GPS spoofing, impossible travel) and traffic spikes.
   - **Implementation**: `src/services/anomaly_service.py`
   - **Endpoints**:
     - `GET /owner/anomalies` – latest anomalies for the owner.
     - `GET /owner/anomalies/summary` – aggregated statistics.

4. **Sentiment Analysis**
   - **Purpose**: Analyse review sentiment (positive/negative) for owners.
   - **Implementation**: Integrated within `chatbot_service` and `review_service` using an external HuggingFace model.
   - **Endpoints**:
     - `GET /owner/reviews?start_date=…&end_date=…` – returns sentiment breakdown.

5. **Dashboard Analytics**
   - **Owner Dashboard** (`src/dashboard/finallll.py` – Streamlit app)
     - KPI cards (visits, saves, calls, directions).
     - Heatmaps and active visitor pins.
     - Review sentiment visualisation.
   - **Admin Dashboard** – similar analytics for platform‑wide metrics.

---

## API Structure

### Mobile API (`/mobile`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Returns JWT `access_token`.
| `/auth/profile` | GET/PUT | Fetch or update the authenticated user profile.
| `/places` | GET | List searchable places (supports `?query=`). |
| `/places/{id}` | GET | Detailed place info with reviews.
| `/properties/my` | GET | Owner’s property listings.
| `/properties/{id}` | GET/PUT/DELETE | CRUD for property items.
| `/categories` | GET | Static place categories.
| `/interactions` | POST | Log visitor interactions (calls, saves, directions).
| `/reviews` | GET/POST/PUT/DELETE | Manage place reviews.
| `/notifications/request` | POST | Create a notification request for approval.

### Owner Dashboard API (`/owner`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/dashboard` | GET | Core KPI data for the owner’s places.
| `/analytics` | GET | Time‑series analytics for visits, saves, etc.
| `/chatbot-stats` | GET | Chatbot usage statistics.
| `/location-heatmap` | GET | Visitor location data for heatmap.
| `/active-visitors` | GET | Real‑time visitor positions.
| `/peak-hour` | GET | Identifies the busiest hour of the day.
| `/location-summary` | GET | Aggregate location metrics.
| `/notifications/requests` | GET | Pending notification requests.
| `/notifications/request` | POST | Submit a new notification request.
| `/opportunities` | GET | AI‑generated business opportunities for the owner.
| `/my-place` & `/my-places` | GET | Retrieve the owner’s primary and secondary locations.
| `/add-branch` | POST | Request to add a new branch (requires admin approval).

---

## Data Store
- **PostgreSQL** with **PostGIS** extensions for spatial queries.
- **Alembic** migrations located in `alembic/`.
- **Redis** (optional) for rate‑limiting and session caching.

---

## Authentication & Authorization
- JWT tokens issued by `/mobile/auth/login`.
- Dependency injection (`get_current_user`) validates tokens on each request.
- Role‑based guards (`admin_guard`, `owner_guard`) enforce access to dashboard routes.

---

## Background Tasks
- FastAPI `BackgroundTasks` used for:
  - Storing interaction logs.
  - Triggering asynchronous anomaly checks.
  - Sending email notifications via `src/utils/email.py`.

---

## Extensibility
- Services are decoupled from repositories, allowing easy swapping of data sources.
- AI services are thin wrappers around external HuggingFace endpoints – simply replace the URL in `.env` to switch models.

---

## Environment Variables (`.env`)
```
SECRET_KEY=...
DATABASE_URL=postgresql://user:pass@db:5432/aroundu
REDIS_URL=redis://redis:6379/0
ENABLE_REDIS=true
SMTP_HOST=...
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
FRONTEND_URL=https://aroundu.com
CORS_ORIGINS=http://localhost:3000
```

---

## Quick Start (Local)
```bash
# Clone repo
git clone <repo-url>
cd AroundU
# Create .env (copy .env.example)
cp .env.example .env
# Build containers
docker compose up --build -d
# Run migrations
alembic upgrade head
# Launch Streamlit dashboard
streamlit run dashboard/finallll.py
```

---

*This document is intended for developers joining the AroundU project to quickly understand the backend capabilities, API surface, and data flow.*
