#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Building bot image"
docker compose build bot

echo "==> Pulling surrealdb image"
docker compose pull surrealdb

echo "==> Restarting services"
docker compose up -d --remove-orphans

echo "==> Waiting for bot health check (up to 60s)"
for i in $(seq 1 30); do
    if curl -sf http://localhost:8080/health >/dev/null 2>&1; then
        echo "==> Bot is healthy"
        exit 0
    fi
    sleep 2
done

echo "==> Health check failed" >&2
docker compose logs bot --tail=50
exit 1
