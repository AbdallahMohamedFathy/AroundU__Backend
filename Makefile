# ─────────────────────────────────────────────────────────────
#  AroundU Backend — Makefile shortcuts
#
#  Run any target with:   make <target>
#  Example:               make up
# ─────────────────────────────────────────────────────────────

.PHONY: help up down dev build logs shell db-shell seed migrate ps clean

# Default target
help:
	@echo ""
	@echo "  AroundU Backend — available commands"
	@echo "  ─────────────────────────────────────────────────"
	@echo "  make up        Start all containers (production mode)"
	@echo "  make down      Stop and remove containers"
	@echo "  make build     Rebuild the API image"
	@echo "  make logs      Follow API logs"
	@echo "  make shell     Open bash inside the API container"
	@echo "  make db-shell  Open psql inside the DB container"
	@echo "  make seed      Seed the database with sample data"
	@echo "  make migrate   Run Alembic migrations"
	@echo "  make ps        Show running containers"
	@echo "  make clean     Remove containers, volumes, and images"
	@echo "  ─────────────────────────────────────────────────"
	@echo ""

# ── Production ───────────────────────────────────────────────
up:
	docker compose --env-file .env.docker up --build -d
	@echo ""
	@echo "✅  AroundU API is running at http://localhost:8000"
	@echo "📖  Swagger docs:  http://localhost:8000/api/docs"
	@echo ""

# ── Stop ─────────────────────────────────────────────────────
down:
	docker compose down

# ── Rebuild image only ────────────────────────────────────────
build:
	docker compose build api

# ── Logs ─────────────────────────────────────────────────────
logs:
	docker compose logs -f api

# ── Shell inside API container ────────────────────────────────
shell:
	docker compose exec api /bin/bash

# ── psql inside DB container ──────────────────────────────────
db-shell:
	docker compose exec db psql -U aroundu_user -d aroundu

# ── Run migrations ────────────────────────────────────────────
migrate:
	docker compose exec api alembic upgrade head

# ── Seed sample data ─────────────────────────────────────────
seed:
	docker compose exec api python scripts/seed_data.py

# ── Show running containers ───────────────────────────────────
ps:
	docker compose ps

# ── Full cleanup (removes volumes = all data) ─────────────────
clean:
	docker compose down -v --rmi local
	@echo "🗑️  All containers, volumes, and local images removed."
