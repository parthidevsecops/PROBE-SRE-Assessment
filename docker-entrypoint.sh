#!/bin/sh
set -eu
echo '=================================================='
echo 'PROBE SRE assessment ingestion'
echo '=================================================='
python /app/startup_ingest.py
echo '=================================================='
echo 'PROBE SRE ready. Chat: http://localhost:8501/  (fallback, no-build UI: http://localhost:8501/debug-chat)'
echo '=================================================='
exec uvicorn api:app --host 0.0.0.0 --port 8501
