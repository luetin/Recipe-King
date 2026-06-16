#!/bin/sh
# Restores the RecipeKing Postgres database from a backup file produced by
# backup.sh. This OVERWRITES all current data.
# Run from the project root on the Debian server: ./scripts/restore.sh backups/recipeking_20260101_120000.sql
set -e

cd "$(dirname "$0")/.."

if [ -z "$1" ]; then
  echo "Usage: ./scripts/restore.sh path/to/backup.sql"
  exit 1
fi

if [ ! -f "$1" ]; then
  echo "File not found: $1"
  exit 1
fi

set -a
. ./.env
set +a

echo "WARNING: this will overwrite ALL current data in the recipeking database with the contents of $1."
printf "Type 'yes' to continue: "
read CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Aborted."
  exit 1
fi

# Drop and recreate the schema so the restore starts from a clean slate,
# then replay the dump.
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$1"

echo "Restore complete."
