#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${1:-http://localhost:8080}"
curl --fail --silent --show-error "$BASE_URL/healthz"
printf '\n'
curl --fail --silent --show-error "$BASE_URL/readyz"
printf '\n'
curl --fail --silent --show-error -X POST "$BASE_URL/api/predict" \
  -H 'Content-Type: application/json' \
  -d '{"text":"Mi transferencia no llegó al destinatario"}'
printf '\n'
