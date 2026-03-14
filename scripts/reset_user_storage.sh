#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STORAGE_DIR="$ROOT/symfony/var/user_storage"

if [ -d "$STORAGE_DIR" ]; then
  rm -rf "$STORAGE_DIR"
  echo "Deleted local user storage: $STORAGE_DIR"
else
  echo "No local user storage directory found at: $STORAGE_DIR"
fi

if [ "${RESET_DB:-}" = "1" ]; then
  if [ -x "$ROOT/symfony/bin/console" ]; then
    echo "Resetting DB tables (file_key_records, user_key_vault)..."
    "$ROOT/symfony/bin/console" doctrine:query:sql "TRUNCATE file_key_records" || true
    "$ROOT/symfony/bin/console" doctrine:query:sql "TRUNCATE user_key_vault" || true
  else
    echo "Symfony console not found; skip DB reset."
  fi
fi

echo "Note: remote storage backends (Dropbox/GDrive/S3/OneDrive) must be cleared manually."
