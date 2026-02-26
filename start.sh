#!/bin/sh

echo "Waiting for database..."

until alembic current >/dev/null 2>&1; do
  sleep 2
done

echo "Running migrations..."
alembic upgrade head

echo "Starting server..."

exec gunicorn \
  -k uvicorn.workers.UvicornWorker \
  -w 4 \
  -b 0.0.0.0:8000 \
  src.main:app
