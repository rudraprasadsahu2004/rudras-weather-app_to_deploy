#!/usr/bin/env bash
# Starts both services for a single Render web service:
#  - FastAPI runs privately on 127.0.0.1:8001 (as designed in flask_app.py)
#  - Flask is the public-facing process, bound to Render's $PORT
set -e

echo "Starting FastAPI backend on 127.0.0.1:8001 ..."
uvicorn fastapi_weather:app --host 127.0.0.1 --port 8001 &

# Give FastAPI a moment to boot before Flask starts proxying to it
sleep 3

echo "Starting Flask frontend on 0.0.0.0:${PORT:-5000} ..."
exec gunicorn flask_app:app --bind "0.0.0.0:${PORT:-5000}" --workers 2 --timeout 30
