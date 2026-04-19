# NutriAI — Clinical Nutrition Platform

A full-stack clinical nutrition recommendation engine powered by machine learning. Provides diet recommendations, health risk scoring, meal planning, and AI-powered consultation.

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
│   │   ├── main.py            ← Startup and Lifespan engine
│   │   ├── routers/           ← API endpoints
│   │   ├── services/          ← ML and logic services
│   │   ├── core/              ← DB, Redis, security
│   │   └── models/            ← SQLAlchemy models
│   ├── requirements.txt
│   ├── Dockerfile
│   └── render.yaml            ← Render.com deployment config
├── frontend/                  ← React + Vite
│   ├── src/
│   │   └── FullStack.jsx      ← Main React app
│   ├── package.json
│   └── vite.config.js
└── vercel.json                ← Vercel deployment config
```

## Local Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs at: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Deployment

### Backend → Render.com

1. Connect GitHub repo to Render
2. Render auto-detects `render.yaml`
3. Add environment variables:
   - `DATABASE_URL` — PostgreSQL connection string
   - `REDIS_URL` — Redis connection string
   - `ALLOWED_ORIGINS` — Your Vercel frontend URL
   - `SECRET_KEY` — Generate a secure key for JWT
4. Deploy as web service

### Frontend → Vercel

1. Import GitHub repo in Vercel
2. Framework preset: Vite
3. Build command: `cd frontend && npm install && npm run build`
4. Output directory: `frontend/dist`
5. Add environment variable: `VITE_API_URL` = your Render backend URL

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/predict` | Full prediction (diet + risk + meals + SHAP + CI) |
| POST | `/predict/diet` | Diet classification only |
| POST | `/predict/risk` | Health risk score with CI |
| POST | `/meals` | Meal recommendations |
| POST | `/chat` | AI clinical consultation |
| GET | `/health` | Service health + model card |
| GET | `/health/metrics` | Model accuracy metrics |

## Example Request

```bash
curl -X POST https://your-render-url.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d '{
    "age": 45,
    "gender": "Male",
    "weight_kg": 75,
    "height_cm": 170,
    "disease_type": "Diabetes",
    "severity": "Moderate",
    "activity_level": "Moderate",
    "daily_caloric": 2200,
    "cholesterol": 210,
    "blood_pressure": 135,
    "glucose": 150,
    "cuisine": "Indian"
  }'
```

## ML Models

| Model | Algorithm | Task | Performance |
|-------|-----------|------|-------------|
| Diet Recommender | Gradient Boosting | Multi-class classification | 100% CV accuracy |
| Risk Scorer | Random Forest Regressor | Continuous risk 0–100 | RMSE 3.93 |
| Meal Categoriser | Random Forest | Multi-class classification | 100% CV accuracy |

**Note:** Trained on 1,000 synthetic patient records. Models use disease type as primary clinical determinant. Production use requires real-world clinical data.

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, Redis
- **ML:** scikit-learn, XGBoost, SHAP
- **Frontend:** React 18, Vite
- **Deployment:** Render (backend), Vercel (frontend)