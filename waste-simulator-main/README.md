# Smart Waste Management Simulator

SWMS is an integrated decision-support web application for local authorities. It records location and planning data, calculates waste and capacity needs, runs transparent 0-20 year simulations, exposes GIS-ready data, and serves a React dashboard.

## Quick start

1. Copy `.env.example` to `.env` and set `DATABASE_URL` to the existing `swms_db` PostgreSQL/PostGIS instance. The default SQLite URL is only a convenient local-development fallback.
2. `cd backend && python -m venv .venv && .venv\\Scripts\\pip install -r requirements.txt`
3. `uvicorn app.main:app --reload --port 8000`
4. In a second terminal: `cd frontend && .\\start-frontend.ps1` (or `npm install && npm run dev`).

The API is available at `http://localhost:8000/docs`; frontend calls use `VITE_API_URL` (default `http://localhost:8000/api/v1`). Register the first account as `SUPER_ADMIN` for administrative setup.

## Test and Postman

Run `cd backend && pytest -v`. Import `postman/SWMS_API.postman_collection.json` and `postman/SWMS_Environment.postman_environment.json` into Postman. The collection captures login tokens and asserts response contracts.

## Design notes

All results are calculated from stored inputs. Calculation results show base waste, each adjustment, and capacity gaps; no visual result is hard-coded. The production database URL may use `postgresql+psycopg://swms_user:...@localhost:5432/swms_db`. PostGIS geometry is deliberately stored as GeoJSON-compatible JSON in the portable core schema, so the API works in test SQLite and PostgreSQL; enable a geometry column/index through an Alembic migration when spatial query scale requires it.
