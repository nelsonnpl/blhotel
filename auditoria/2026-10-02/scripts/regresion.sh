#!/bin/sh
# regresion.sh — pytest con base temporal propia + Node + QA + capturas.
# Corre en segundo plano con log (lo lanza el director). Uso: sh regresion.sh [base] [out]
set -eu
BASE="${1:-http://127.0.0.1:5060}"
OUT="${2:-artifacts/visual-qa/pulido/regresion}"
TMPDB="$(mktemp -t atlas-reg-XXXX.sqlite)"
export SQLITE_PATH="$TMPDB"
cp ./data/booking-prices.sqlite "$TMPDB"
mkdir -p "$OUT"
echo "== pytest =="; .venv/bin/python -m pytest -q || exit 1
echo "== node =="; node --test tests/*.cjs 2>/dev/null || npm test --prefix tests 2>/dev/null || echo "node: revisar tests/index.js"
echo "== e2e =="; .venv/bin/python tests/e2e/shoot.py --base "$BASE" --out "$OUT" || exit 1
echo "OK regresion out=$OUT tmpdb eliminada"; rm -f "$TMPDB"
