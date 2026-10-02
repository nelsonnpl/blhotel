#!/bin/sh
# estado_jobs.sh — solo lectura: jobs queued/running en la base indicada.
# Uso: sh estado_jobs.sh [base.sqlite] (defecto ./data/booking-prices.sqlite)
set -eu
DB="${1:-./data/booking-prices.sqlite}"
sqlite3 -readonly "$DB" "SELECT status, COUNT(*) FROM background_jobs GROUP BY status;" 2>/dev/null \
  || sqlite3 -readonly "$DB" ".tables"
