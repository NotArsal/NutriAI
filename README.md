# NutriAI — Clinical Nutrition Platform

## Architecture

```
nutriai/
├── ml/                     ← Trained model artifacts
│   ├── diet_model.pkl      ← GBM classifier (diet recommendation)
│   ├── risk_model.pkl      ← RF regressor (health risk score)
│   ├── meal_model.pkl      ← RF classifier (meal category)
│   ├── feature_cols.pkl    ← Feature column order
│   └── model_meta.json     ← Encoder maps + accuracy stats
├── backend/
│   ├── main.py             ← FastAPI application
│   └── requirements.txt
└── frontend/
    └── src/
        └── FullStack.jsx     ← React frontend (full-stack)
```

## Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs at: http://localhost:8000/docs

### Key endpoints

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/predict` | Full prediction (diet + risk + meals) |
| POST | `/predict/diet` | Diet recommendation only |
| POST | `/predict/risk` | Health risk score only |
| POST | `/meals` | Meal recommendations only |
| GET | `/health` | Service health check |
| GET | `/models/info` | Model accuracy stats |

### Example request

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "age": 45, "gender": "Male",
    "weight_kg": 75, "height_cm": 170,
    "disease_type": "Diabetes", "severity": "Moderate",
    "activity_level": "Moderate",
    "daily_caloric": 2200, "cholesterol": 210,
    "blood_pressure": 135, "glucose": 150,
    "cuisine": "Indian"
  }'
```

## ML Models

| Model | Algorithm | Task | Performance |
|-------|-----------|------|-------------|
| Diet Recommender | Gradient Boosting | Multi-class classification | 100% CV accuracy |
| Risk Scorer | Random Forest Regressor | Continuous risk 0–100 | RMSE 3.93 |
| Meal Categoriser | Random Forest | Multi-class classification | 100% CV accuracy |

Trained on 1,000 patient records. The diet model achieves perfect accuracy because disease type is the primary clinical determinant — consistent with clinical nutrition guidelines.
