.PHONY: setup-web setup-api dev-web dev-api test build docker-up migrate

setup-web:
	npm install

setup-api:
	cd apps/api && python -m venv .venv && .venv/Scripts/python -m pip install -U pip && .venv/Scripts/python -m pip install -e ".[dev]"

dev-web:
	npm run dev:web

dev-api:
	npm run dev:api

test:
	npm run test:web && npm run test:api

build:
	npm run build:web

docker-up:
	docker compose up --build

migrate:
	cd apps/api && alembic upgrade head
