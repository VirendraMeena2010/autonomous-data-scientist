#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required" >&2
  exit 1
fi

if [[ -z "${BACKUP_DIR:-}" ]]; then
  echo "BACKUP_DIR is required" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_file="$BACKUP_DIR/ads-$timestamp.dump"

# Supports postgres:// and postgresql:// URLs.
pg_dump "$DATABASE_URL" \
  --format=custom \
  --file="$backup_file" \
  --no-owner \
  --no-privileges

echo "$backup_file"
