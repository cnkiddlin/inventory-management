#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -x .venv/bin/python ]]; then
  echo "未找到 .venv，正在创建虚拟环境..."
  python3 -m venv .venv
fi

if ! .venv/bin/python -c "import fastapi, sqlalchemy, alembic, psycopg" >/dev/null 2>&1; then
  echo "正在安装后端依赖..."
  .venv/bin/pip install -r backend/requirements-dev.txt
fi

if [[ ! -d frontend/node_modules ]]; then
  echo "正在安装前端依赖..."
  (cd frontend && npm install)
fi

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "启动库存管理系统 API: http://localhost:8000"
echo "Swagger UI:          http://localhost:8000/docs"
echo "前端应用:            http://localhost:5173"
(cd backend && ../.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!

cd frontend
npm run dev -- --host 0.0.0.0
