#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

if [ ! -d "$BACKEND_DIR/.venv" ]; then
  echo "Creating backend virtual environment..."
  cd "$BACKEND_DIR"
  python3 -m venv .venv
fi

cd "$BACKEND_DIR"
source .venv/bin/activate

if [ -f "$BACKEND_DIR/.env" ]; then
  set -a
  source "$BACKEND_DIR/.env"
  set +a
fi

python -m pip install -r requirements.txt >/dev/null 2>&1 || true

if ! pgrep -f "uvicorn app.main:app --host 0.0.0.0 --port 8000" >/dev/null 2>&1; then
  echo "Starting backend on http://localhost:8000"
  nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "$ROOT_DIR/backend.log" 2>&1 &
fi

cd "$FRONTEND_DIR"
if [ ! -d node_modules ]; then
  echo "Installing frontend dependencies..."
  npm install
fi

echo "Starting frontend on http://localhost:5173"
nohup npm run dev -- --host 0.0.0.0 > "$ROOT_DIR/frontend.log" 2>&1 &

echo "Project is running."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
