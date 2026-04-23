# NutriAI — Clinical Nutrition Platform

A full-stack clinical nutrition recommendation engine powered by machine learning. Provides personalised diet recommendations, health risk scoring, meal planning, and AI-powered consultation — with **full multi-user support**, secure JWT authentication, and per-user prediction history.

## Architecture

```
nutriai/
├── ml/                        ← Trained model artifacts
│   ├── diet_model.pkl         ← GBM classifier (diet recommendation)
│   ├── risk_model.pkl         ← RF regressor (health risk score)
│   ├── meal_model.pkl         ← RF classifier (meal category)
│   ├── feature_cols.pkl       ← Feature column order
│   └── model_meta.json        ← Encoder maps + accuracy stats
├── backend/                   ← FastAPI application
│   ├── app/
│   │   ├── main.py            ← App factory, lifespan, global error handlers
│   │   ├── config.py          ← Pydantic-settings (all env vars)
│   │   ├── routers/           ← API route handlers
│   │   │   ├── auth.py        ← Register, login, profile management
│   │   │   ├── predict.py     ← Full / diet-only / risk-only predictions
│   │   │   ├── meals.py       ← Meal recommendations
│   │   │   ├── chat.py        ← AI clinical consultation
│   │   │   ├── reports.py     ← Per-user prediction history (CRUD)
│   │   │   └── health.py      ← Health check + model card
│   │   ├── models/            ← SQLAlchemy ORM models
│   │   │   ├── user.py        ← User (id, email, full_name, role, …)
│   │   │   └── prediction.py  ← PredictionLog (user-scoped history)
│   │   ├── schemas/           ← Pydantic request/response models
│   │   │   ├── user.py        ← UserCreate, UserOut, UserUpdate, reports
│   │   │   ├── patient.py     ← PatientInput (validated biomarkers)
│   │   │   └── responses.py   ← PredictResponse, RiskResponse, …
│   │   ├── repositories/      ← Async DB access layer
│   │   │   ├── user_repo.py   ← CRUD for User
│   │   │   └── prediction_repo.py ← CRUD + per-user history queries
│   │   ├── api/
│   │   │   └── deps.py        ← FastAPI DI: get_db, get_current_user, …
│   │   ├── services/          ← Business logic
│   │   │   ├── ml_service.py  ← Model inference (diet, risk, meal, SHAP)
│   │   │   └── chat_service.py← Rule-based clinical chat
│   │   └── core/
│   │       ├── database.py    ← SQLAlchemy async engine (NullPool)
│   │       ├── security.py    ← bcrypt hashing, JWT encode/decode
│   │       ├── redis_client.py← Redis caching client
│   │       └── logging.py     ← structlog + request-ID middleware
│   └── requirements.txt
├── frontend/                  ← React + Vite
│   ├── src/
│   │   └── FullStack.jsx      ← Entire SPA (auth, dashboard, history, …)
│   ├── package.json
│   └── vite.config.js
├── Dockerfile
├── docker-compose.yml
├── render.yaml                ← Render.com deployment config
└── vercel.json                ← Vercel deployment config
```

## Features

- **Multi-user accounts** — register, login, update profile, deactivate account
- **JWT authentication** — Bearer tokens stored in `localStorage`; auto-refreshed on page load
- **Per-user prediction history** — paginated report list, single report detail, delete
- **Data isolation** — every query is scoped to `WHERE user_id = current_user.id`
- **Graceful DB degradation** — predictions work without a database; auth/history return HTTP 503 with a friendly message instead of crashing
- **ML inference** — diet classification, health risk scoring (0–100 with 90% CI), meal recommendations, SHAP explainability
- **AI consultation** — context-aware clinical chat seeded with patient biomarkers
- **Rate limiting** — per-IP via slowapi; configurable per route
- **Redis caching** — 24-hour prediction result cache keyed on input hash

## Local Development

### Prerequisites

| Service | Purpose | Required? |
|---------|---------|-----------|
| Python 3.11+ | Backend | ✅ |
| Node 18+ | Frontend | ✅ |
| PostgreSQL 15+ | Auth & history | Optional (auth returns 503 without it) |
| Redis | Prediction cache | Optional (silently skipped) |

### Backend

```bash
cd backend
pip install -r requirements.txt

# Copy and edit environment variables
cp .env.example .env   # or create manually (see Environment Variables below)

uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

### Environment Variables

Create `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/nutriplanner
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-in-production-use-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080   # 7 days
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:4173
ENVIRONMENT=development
```

> **Without a database:** The app starts normally. `/predict`, `/meals`, `/chat`, and `/health` all work. `/auth/*` and `/reports` return HTTP 503 with a clear message.

## Database Migrations

The app auto-creates tables on startup in development (`Base.metadata.create_all`).  
For production, use Alembic:

```bash
cd backend
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

## Deployment

### Backend → Render.com

1. Connect GitHub repo to Render
2. Render auto-detects `render.yaml`
3. Attach a **PostgreSQL** database add-on (optional but recommended)
4. Add environment variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg scheme) |
| `REDIS_URL` | Redis connection string |
| `SECRET_KEY` | Long random string for JWT signing (`openssl rand -hex 32`) |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed frontend origins |
| `ENVIRONMENT` | `production` |

### ▲ Vercel (Frontend)

1. Go to **vercel.com → Add New Project** → import the GitHub repo.
2. In **Configure Project**, set:
   - **Root Directory**: `frontend`  <-- **CRITICAL STEP**
   - **Framework Preset**: Vite
3. Add **Environment Variable**: `VITE_API_URL` = your Render service URL (e.g. `https://nutriplanner-api.onrender.com`).
4. Click **Deploy**.

> **Note:** If you get a 404 error after deployment, ensure the **Root Directory** is set to `frontend` in the project settings.

## 🛠️ Troubleshooting & Fixes

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for a detailed list of common deployment errors (CORS, Database Connections, Vercel 404s) and how we solved them.

### Public (no auth required)

| Method | Route | Description |
|--------|-------|-------------|
| `POST` | `/predict` | Full prediction (diet + risk + meals + SHAP + CI) |
| `POST` | `/predict/diet` | Diet classification only |
| `POST` | `/predict/risk` | Health risk score with 90% CI |
| `POST` | `/meals` | Meal recommendations |
| `POST` | `/chat` | AI clinical consultation |
| `GET` | `/health` | Service health + model card |
| `GET` | `/health/metrics` | Model accuracy + confusion matrix |

### Auth (no token needed)

| Method | Route | Description |
|--------|-------|-------------|
| `POST` | `/auth/register` | Create a new account |
| `POST` | `/auth/login` | Login → returns JWT access token |

### Protected (Bearer token required)

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/auth/me` | Get current user's profile |
| `PUT` | `/auth/me` | Update name / email / password |
| `DELETE` | `/auth/me` | Deactivate account |
| `GET` | `/reports` | Paginated prediction history (current user only) |
| `GET` | `/reports/{id}` | Single report detail |
| `DELETE` | `/reports/{id}` | Delete a report |

## Example: Register & Predict (authenticated)

```bash
# 1. Register
curl -X POST https://your-render-url.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "secret123", "full_name": "Dr. Smith"}'

# 2. Login → get token
TOKEN=$(curl -s -X POST https://your-render-url.onrender.com/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=you@example.com&password=secret123" | jq -r .access_token)

# 3. Predict (saves to your history)
curl -X POST https://your-render-url.onrender.com/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "age": 45, "gender": "Male", "weight_kg": 75, "height_cm": 170,
    "disease_type": "Diabetes", "severity": "Moderate",
    "activity_level": "Moderate", "daily_caloric": 2200,
    "cholesterol": 210, "blood_pressure": 135, "glucose": 150,
    "cuisine": "Indian"
  }'

# 4. View your history
curl https://your-render-url.onrender.com/reports \
  -H "Authorization: Bearer $TOKEN"
```

## ML Models

| Model | Algorithm | Task | Performance |
|-------|-----------|------|-------------|
| Diet Recommender | Gradient Boosting | Multi-class classification | 100% CV accuracy |
| Risk Scorer | Random Forest Regressor | Continuous risk 0–100 | RMSE 3.93 |
| Meal Categoriser | Random Forest | Multi-class classification | 100% CV accuracy |

**Note:** Trained on 1,000 synthetic patient records. Models use disease type as the primary clinical determinant. Production use requires validation on real-world clinical data.

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy (async + NullPool), PostgreSQL, Redis, slowapi
- **Auth:** JWT (PyJWT), bcrypt (passlib)
- **ML:** scikit-learn, XGBoost, SHAP
- **Frontend:** React 18, Vite
- **Deployment:** Render (backend), Vercel (frontend)