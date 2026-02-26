#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  AroundU — Container entrypoint script
#
#  Order of operations:
#    1. Wait until PostgreSQL is accepting connections
#    2. Run Alembic migrations (safe to run repeatedly)
#    3. (Optional) Seed the DB if it's empty
#    4. Start uvicorn
# ─────────────────────────────────────────────────────────────

set -e  # exit immediately on any error

echo "========================================"
echo "  AroundU API — starting up"
echo "========================================"

# ── 1. Wait for PostgreSQL ────────────────────────────────────
echo "Waiting for PostgreSQL to be ready..."

MAX_RETRIES=30
RETRY=0

until python -c "import psycopg, os, sys; psycopg.connect(os.environ['DATABASE_URL']).close()" 2>/dev/null; do
    RETRY=$((RETRY + 1))
    if [ "$RETRY" -ge "$MAX_RETRIES" ]; then
        echo "PostgreSQL not available after ${MAX_RETRIES} retries. Exiting."
        exit 1
    fi
    echo "   Attempt ${RETRY}/${MAX_RETRIES} — retrying in 2s..."
    sleep 2
done

echo "PostgreSQL is ready."

# ── 2. Run Alembic migrations ─────────────────────────────────
echo ""
echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete."

# ── 3. Seed data (only if SEED_DB=true) ──────────────────────
if [ "${SEED_DB:-false}" = "true" ]; then
    echo ""
    echo "Seeding database with sample data..."
    python scripts/seed_data.py
    echo "Seeding complete."
fi

# ── 4. Start the API ──────────────────────────────────────────
echo ""
echo "Starting AroundU API on port 8000..."
echo "   Docs: http://localhost:8000/api/docs"
echo "========================================"

# In production mode, run with strict settings (no debug, no SQL echo)
exec gunicorn -k uvicorn.workers.UvicornWorker -w "${WORKERS:-4}" -b 0.0.0.0:8000 src.main:app
