#!/usr/bin/env bash
# Local dev convenience: brings up Postgres + the backend via Docker, then
# runs the frontend with a plain static server so you get instant reloads
# on save (no container rebuild needed while editing frontend/src/).
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "No .env found — copying .env.example. Fill in any keys you have before running a real scan."
  cp .env.example .env
fi

echo "Starting db + backend (docker compose)…"
docker compose up --build -d db backend

echo "Waiting for the backend to report healthy…"
until curl -sf http://localhost:8000/health > /dev/null; do sleep 1; done
echo "Backend is up: http://localhost:8000/docs"

echo "Serving the frontend statically on http://localhost:5173 (Ctrl+C to stop)…"
cd frontend
npx --yes serve -l 5173 .
