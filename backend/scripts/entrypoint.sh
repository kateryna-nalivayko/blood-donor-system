#!/bin/bash
set -e

# Install netcat if not already installed
apt-get update && apt-get install -y netcat-openbsd

# Only wait for Postgres in Docker environment
if [ "$DB_HOST" = "db" ] && [ "$DB_NAME" = "BloodDonorSystemDB" ]; then
    echo "Docker environment detected. Waiting for PostgreSQL..."
    while ! nc -z "$DB_HOST" "$DB_PORT"; do
      sleep 0.5
      echo "Still waiting for PostgreSQL..."
    done
    echo "PostgreSQL started"
else
    echo "Skipping PostgreSQL wait (not in Docker or using different database)"
fi

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting application..."
exec "$@"