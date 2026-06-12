#!/usr/bin/env bash
# Start the FastAPI backend (:8000) and the Vite UI dev server (:5173)
# together for local development. Stop both with Ctrl+C.
#
# Usage:
#   ./startup.sh

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load .env (Pioneer / ClickHouse credentials) into the environment.
if [ -f "$ROOT_DIR/.env" ]; then
  set -a
  source "$ROOT_DIR/.env"
  set +a
fi

# --- Backend (FastAPI on :8000) ---
cd "$ROOT_DIR/Backend"

if [ -f .venv/Scripts/activate ]; then
  source .venv/Scripts/activate
elif [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

echo "Starting backend (uvicorn) on :8000..."
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

cleanup() {
  echo ""
  echo "Stopping backend (pid $BACKEND_PID)..."
  kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Waiting for backend health check..."
for _ in $(seq 1 30); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend is up."
    break
  fi
  sleep 0.5
done

# --- UI (Vite on :5173, proxies /negotiations and /health to :8000) ---
cd "$ROOT_DIR/UI"

if [ ! -d node_modules ]; then
  echo "Installing UI dependencies..."
  npm install
fi

echo "Starting UI (vite) on :5173..."
npm run dev
