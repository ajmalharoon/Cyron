#!/bin/sh
# Runs automatically (nginx's /docker-entrypoint.d/ convention) before nginx
# starts, so the frontend can read its backend URL and API key from the
# environment at container start rather than at build time.
set -eu

OUT=/usr/share/nginx/html/env.js
API_BASE="${CYRON_API_BASE:-http://localhost:8000}"
API_KEY="${CYRON_API_KEY:-}"

cat > "$OUT" <<JS
window.CYRON_ENV = {
  apiBase: "${API_BASE}",
  apiKey: "${API_KEY}"
};
JS

echo "cyron: wrote env.js (apiBase=${API_BASE})"
