#!/bin/sh

echo "Waiting for database..."

until alembic current >/dev/null 2>&1; do
  sleep 2
done

echo "Running migrations..."
alembic upgrade head

# Write Firebase credentials file from env var if provided
if [ -n "$FIREBASE_SERVICE_ACCOUNT_JSON" ]; then
  echo "$FIREBASE_SERVICE_ACCOUNT_JSON" > /app/firebase-credentials.json
  echo "Firebase credentials file created from env var."
fi

echo "Starting server..."

exec gunicorn \
  -k uvicorn.workers.UvicornWorker \
  -w 4 \
  -b 0.0.0.0:8000 \
  src.main:app
