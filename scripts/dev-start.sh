#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "[dev-start] Missing required command: uv"
  exit 1
fi

FRONTEND_PM=""
if command -v pnpm >/dev/null 2>&1; then
  FRONTEND_PM="pnpm"
elif command -v npm >/dev/null 2>&1; then
  FRONTEND_PM="npm"
else
  echo "[dev-start] Missing frontend package manager (pnpm or npm)."
  exit 1
fi

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

echo "[dev-start] Starting FastAPI on http://127.0.0.1:8000"
uv run uvicorn src.adapters.interface.http_api.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

sleep 1

echo "[dev-start] Starting frontend with ${FRONTEND_PM} on http://127.0.0.1:5173"
cd "$ROOT_DIR/frontend"
if [[ "$FRONTEND_PM" == "pnpm" ]]; then
  pnpm dev
else
  npm run dev
fi
