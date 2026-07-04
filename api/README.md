# API Contract

Base URL: `http://localhost:8000`

- `GET /api/health`: service health and synthetic-only flag.
- `GET /api/research-summary`: crop profile parameters and source list.
- `POST /api/seasons/generate`: creates a synthetic season, trains models, saves payload to SQLite.
- `GET /api/seasons`: recent saved synthetic seasons.
- `GET /api/seasons/{season_id}`: full saved payload.
- `POST /api/compare`: compares low-noise and high-noise synthetic seasons.

The API never returns or stores real satellite data.
