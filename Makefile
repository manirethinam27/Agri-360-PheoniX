.PHONY: run test backend frontend

run:
	docker compose up --build

test:
	cd backend && pytest -q

backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev -- --host 0.0.0.0
