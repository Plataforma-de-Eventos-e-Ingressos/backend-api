#!/bin/bash
set -e
echo "🚀 Rodando migrações do banco de dados (Alembic)..."
alembic upgrade head
echo "🌱 Populando o banco de dados (Seed)..."
python seed.py
echo "🔥 Iniciando o servidor FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
