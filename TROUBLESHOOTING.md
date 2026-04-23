# NutriAI Troubleshooting Guide

This document tracks common errors encountered during the deployment of the NutriAI platform to Render (Backend) and Vercel (Frontend).

---

## 1. Backend: `ModuleNotFoundError: No module named 'psycopg2'`
**Error:** The app crashes on Render with a missing database driver error.
**Cause:** 
* Render provides a `DATABASE_URL` starting with `postgres://`.
* SQLAlchemy defaults to `psycopg2` for this scheme, which is a synchronous driver.
* Since our app is **async**, it requires `asyncpg`.
**Fix:**
* We added a **Field Validator** in `app/config.py` that automatically detects `postgres://` or `postgresql://` and converts it to `postgresql+asyncpg://`.
* This ensures Render's provided URL works perfectly without manual changes.

---

## 2. Backend: `ConnectionRefusedError` (HTTP 500)
**Error:** The whole app crashes if the PostgreSQL database is down or not yet attached.
**Cause:** The database connection pool was trying to "ping" the database as soon as the app started.
**Fix:**
* Switched the database engine to use `NullPool` in `app/core/database.py`. This prevents the app from holding idle connections and allows it to start even if the DB is unreachable.
* Updated `get_db` dependency in `app/api/deps.py` to catch connection errors and return a clean **HTTP 503 Service Unavailable** message instead of a 500 crash.

---

## 3. Frontend: Vercel `404: NOT_FOUND`
**Error:** The website shows a Vercel 404 page when you visit it or refresh the page.
**Cause:** Vercel didn't know how to handle "Client-Side Routing" (React Router) in a subdirectory monorepo.
**Fix:**
1. Moved `vercel.json` inside the `frontend/` folder.
2. Added a `rewrites` rule to `vercel.json` to redirect all non-API traffic to `index.html`.
3. **Critical:** In Vercel Dashboard Settings, set the **Root Directory** to `frontend`.

---

## 4. Frontend: Login Fails / CORS Errors
**Error:** You can see the site, but logging in or registering gives a "Network Error" or "CORS Error".
**Cause:**
* The Backend (Render) doesn't trust the Frontend (Vercel) URL.
* Or, there is a **trailing slash** in the `ALLOWED_ORIGINS` variable.
**Fix:**
* Go to **Render Dashboard** → **Environment**.
* Ensure `ALLOWED_ORIGINS` is exactly `https://your-site.vercel.app` (**NO** slash at the end).
* Ensure Vercel's `VITE_API_URL` is pointing to the correct Render URL.

---

## 5. ML: `shap_init_failed` Warning
**Warning:** SHAP TreeExplainer fails on certain multiclass models.
**Explanation:** This is a limitation of the SHAP library's TreeExplainer with specific multi-class models like XGBoost.
**Fix:** We implemented a try/except block in the `ml_service.py`. The app will gracefully disable SHAP explanations for that specific model but will continue to provide accurate predictions and risk scores.

---

## 6. Backend: `ImportError: cannot import name 'MODEL_CARD_DATA'`
**Error:** The Render deployment fails and exits with status 1.
**Cause:** The metadata variable `MODEL_CARD_DATA` was missing from `ml_service.py`, causing the `/health` endpoint router to crash on import.
**Fix:** Restored `MODEL_CARD_DATA` and compatibility dictionaries (`meal_classes`, `meta`) inside `app/services/ml_service.py`. The API router can now query the model's properties safely.
