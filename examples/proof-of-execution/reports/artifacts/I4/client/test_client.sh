#!/usr/bin/env bash
# Scripted client verification (requires service on :8000 or skips with note)
set -euo pipefail
BASE="${CONVERT_URL:-http://127.0.0.1:8000}"
if ! curl -sf "${BASE}/health" >/dev/null 2>&1; then
  echo "SKIP: service not running at ${BASE} — start with: uvicorn main:app --port 8000"
  exit 0
fi
node index.js 100 USD EUR | grep -q Result
node index.js 50 EUR GBP | grep -q Rate
echo "client tests OK"
